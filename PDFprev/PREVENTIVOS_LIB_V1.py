import pymupdf
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
import math
import tempfile
import os
import re
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.colors import HexColor


# Variables globales para los archivos seleccionados
# ************* NO UTILIZADAS EN SERVIDOR PARA MAYOR ROBUSTES EN LA CONCURRENCIA ****************
#archivo_pdf = None
#archivo_excel = None
#archivo_salida = None
# ****************************** DESCOMENTAR EN OTROS CASOS *************************************

def decimal_a_horas(decimal):
    # Obtener la parte entera (horas)
    horas = int(decimal)
    # Calcular los minutos
    minutos = int((decimal - horas) * 60)
    segundos = int(((decimal - horas) * 60 - minutos) * 60)
    horario= f"{horas:02d}:{minutos:02d}:{segundos:02d}"
   
    return horario


#Funcion poder encontrar variaciones de palabras con espacios
def palabra_a_regex(palabra):
    patron = r'\s*'.join(map(re.escape, palabra)) 
    return patron
#Funcion encontar datos del texto para TABLAS
def Data_txt(cadena, palabra, aparicion, direccion, numero):
    patron = palabra_a_regex(palabra)
    if (not direccion) and numero:
        coincidencias = [m.start() for m in re.finditer(patron, cadena, flags=re.IGNORECASE)]
        
        if len(coincidencias) < aparicion:
            #No se encuentran datos
            return "---"
        
        indice = coincidencias[aparicion - 1]
        salto_linea = cadena.rfind('\n', 0, indice)
        if salto_linea == -1:
            inicio = 0
        else:
            inicio = salto_linea + 1
        
        if cadena[inicio:indice][0].isdigit():
            return cadena[inicio:indice]
        else:
            return "---"

    if direccion and numero:
        match = re.search(patron, cadena, flags=re.IGNORECASE)
        if match:
            indiceI = match.start()
            indiceF = cadena.find("\n", indiceI + len(match.group()))
            if cadena[indiceI + len(match.group()):indiceF][0].isdigit():
                return cadena[indiceI + len(match.group()):indiceF]
            else:
                return "---"
        else:
            return "---"

    if direccion and not numero:
        coincidencias = [m.start() for m in re.finditer(patron, cadena, flags=re.IGNORECASE)]
        if len(coincidencias) < aparicion:
            #No se encuentran datos
            return "---"
        indiceI = coincidencias[aparicion - 1]
        indiceF = cadena.find("\n", indiceI + len(palabra))
        return cadena[indiceI + len(palabra):indiceF]

def eliminar_fechas_ES(texto):
    # Formato de fechas dinámico: dd/mm/aa o dd/mm/aaaa
    patron = r'\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12][0-9]|3[01])/(\d{2}|\d{4})\b'
    # Encontrar todas las coincidencias y sus índices
    coincidencias = list(re.finditer(patron, texto))
    if not coincidencias:
        return texto  # No hay coincidencias, devolver original  
    # Procesar de atrás hacia adelante para no afectar índices
    texto_modificado = texto
    for match in reversed(coincidencias):
        InicioFecha = match.start()  # Inicio de la fecha
        # Buscar el siguiente salto de línea después del inicio
        FinFecha = texto_modificado.find('\n', InicioFecha)
        if FinFecha == -1:  # Si no hay salto de línea, ir al final del texto
            FinFecha = len(texto_modificado)
        else:
            FinFecha += 1  # Incluir el salto de línea
        # Eliminar el segmento desde inicio hasta fin
        texto_modificado = texto_modificado[:InicioFecha] + texto_modificado[FinFecha:]
    return texto_modificado


def eliminar_paginas_ES(texto):
    # Patrón para números de página en formato n/m seguido de \n\x0c
    patron = r'\b\d+/\d+\n\x0c'
    # Encontrar todas las coincidencias y sus índices
    coincidencias = list(re.finditer(patron, texto))
    if not coincidencias:
        return texto  # No hay coincidencias, devolver original
    # Procesar de atrás hacia adelante para no afectar índices
    texto_modificado = texto
    for match in reversed(coincidencias):
        InicioPagina = match.start()  # Inicio del patrón
        FinPagina = match.end()       # Fin del patrón
        # Eliminar solo el segmento exacto del patrón
        texto_modificado = texto_modificado[:InicioPagina] + texto_modificado[FinPagina:]
    return texto_modificado

def eliminar_fechas_EN(texto):
    # Patrón para fechas en formato dd/mm/AAAA seguido de \n\x0c
    patron = r'\b\d{2}/\d{2}/\d{4}\n\x0c'
    # Encontrar todas las coincidencias y sus índices
    coincidencias = list(re.finditer(patron, texto))
    if not coincidencias:
        return texto  # No hay coincidencias, devolver original
    # Procesar de atrás hacia adelante para no afectar índices
    texto_modificado = texto
    for match in reversed(coincidencias):
        InicioFecha = match.start()  # Inicio del patrón
        FinFecha = match.end()       # Fin del patrón
        # Eliminar solo el segmento exacto del patrón
        texto_modificado = texto_modificado[:InicioFecha] + texto_modificado[FinFecha:]
    return texto_modificado


def Limpieza_Texto(tex, Engl):
    if Engl:
        #tex=eliminar_fechas_EN(tex)
        DatCl = ["Faurecia", "https://", "Additional Tasks", "Page"]
        for d in DatCl:
            while tex.find(d) != -1:
                EI = tex.find(d)
                EF = tex.find("\n", EI) 
                if EF == -1: 
                    tex = tex[:EI]
                else:
                    tex = tex[:EI] + tex[EF+1:]
        tex=eliminar_fechas_EN(tex)
        return tex
    else:
        #tex=eliminar_fechas_ES(tex)
        #tex=eliminar_paginas_ES(tex)
        DatCl=["Faurecia","https://","Tarea Adicional","Page"]
        for d in DatCl:
            while tex.find(d) != -1:
                EI = tex.find(d)
                EF = tex.find("\n", EI) 
                if EF == -1: 
                    tex = tex[:EI]
                else:
                    tex = tex[:EI] + tex[EF+1:]
        tex=eliminar_fechas_ES(tex)
        tex=eliminar_paginas_ES(tex)
        return tex
        

def regexN(Nombre):
    nombre_parts = Nombre.split()
    nombre_regex = r'\s*'.join(re.escape(part) for part in nombre_parts)
    return rf'\s*{nombre_regex}\s*'

#Funcion para ajustar texto
def ajustar_texto(texto, ancho_maximo, fuente="Helvetica", tamano_fuente=12):
    """
    Divide un texto en líneas para que cada línea no supere un ancho máximo en puntos.

    :param texto: El texto a procesar (cadena).
    :param ancho_maximo: El ancho máximo permitido para cada línea en puntos.
    :param fuente: La fuente utilizada para calcular el ancho del texto (por defecto "Helvetica").
    :param tamano_fuente: El tamaño de la fuente en puntos (por defecto 12).
    :return: Texto dividido en líneas con "\n" para respetar el ancho máximo.
    """
    palabras = texto.split()  # Dividir el texto en palabras
    linea_actual = ""
    resultado = ""

    for palabra in palabras:
        # Calcular el ancho de la línea si se añade la palabra actual
        ancho_linea = pdfmetrics.stringWidth(linea_actual + " " + palabra, fuente, tamano_fuente)

        # Si el ancho supera el límite, añadir un salto de línea
        if linea_actual and ancho_linea > ancho_maximo - 2:
            resultado += linea_actual.strip() + "\n"  # Añadir la línea actual al resultado
            linea_actual = palabra  # Comenzar una nueva línea con la palabra actual
        else:
            # Añadir la palabra a la línea actual
            linea_actual += " " + palabra if linea_actual else palabra

    # Añadir la última línea al resultado
    if linea_actual:
        resultado += linea_actual.strip()

    return resultado

#Funcion para instertar imagen
def insertar_imagen(canva,ruta, Ancho, Alto, x, y):    
    image_path = ruta

    # Definir el tamaño de la imagen
    img_width = Ancho  # Ancho de la imagen
    img_height = Alto  # Alto de la imagen

    # Posición de la imagen en la esquina superior derecha
    img_pos_x = x # Ajuste 10 unidades del borde derecho
    img_pos_y = y  # Ajuste 10 unidades del borde superior

    # Insertar la imagen en la posición especificada
    canva.drawImage(image_path, img_pos_x, img_pos_y, img_width, img_height)

# Función para cargar un archivo PDF
#********* REDUNDANTE EN SERVIDOR PUES RECIBE DIRECTAMENTE LOS ARCHIVOS CON HTTP POST **********
"""
def cargar_pdf():
    global archivo_pdf
    archivo_pdf = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
   if archivo_pdf:
        messagebox.showinfo("Archivo PDF", f"Archivo cargado: {archivo_pdf}")
"""
# ****************************** DESCOMENTAR EN OTROS CASOS *************************************

# Función para cargar un archivo Excel
#*********** REDUNDANTE EN SERVIDOR PUES RECIBE DIRECTAMENTE LOS ARCHIVOS CON HTTP POST **********
"""
def cargar_excel():
    global archivo_excel
    archivo_excel = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
    if archivo_excel:
        messagebox.showinfo("Archivo CSV", f"Archivo cargado: {archivo_excel}")
"""
# ****************************** DESCOMENTAR EN OTROS CASOS *************************************




# Función para procesar los archivos cargados
#************ MODIFICACION PARA RECIBIR ARGUMENTOS Y AUMENTAR ROBUSTEZ EN LA CONCUREENCIA ************
def procesar_archivos(archivo_pdf,archivo_excel):
    try:
        # Leer los bytes del PDF desde el objeto FileStorage
        pdf_bytes = archivo_pdf.read()
        # Abrir el PDF desde los bytes en memoria usando BytesIO
        doc = pymupdf.open(stream=BytesIO(pdf_bytes), filetype="pdf")

        # Procesar el archivo Excel
        df = pd.read_csv(archivo_excel)

        text_buffer = StringIO()
        for page in doc:
            text = page.get_text()
            text_buffer.write(text)
            text_buffer.write('\f')  # Separador de página (equivalente a bytes((12,)))
        texto = text_buffer.getvalue()
        text_buffer.close()

        
        task=[]
        for t in df.DS_WORK_OPERA:
            task.append(t)
        
        Engl="Breakdown Log Sheet" in texto
        EnVars=["User: ","UAP: ","Equipment/Tool: ","Order: ","Equip/Tool ref: ","Machine Stopped\nDate\nTime\n","\nGap Leader","Gap Leader\nName\n","Start Intervention\nDate\nTime\n","\nMaintenance Intervener\nName\n","Maintenance Intervener\nName\n","End Intervention\nDate\nTime\n","\nMaintenance Intervener\nName\n","Maintenance Intervener\nName\n","Machine Restart\nDate\nTime\n","\nGap Leader","Gap Leader\nName\n","Description of the Breakdown\n","Actions Done to Restart\n","\nRoot Cause Confirmed"]
        EsVars=["User: ","UAP: ","Equipo/Molde: ","Orden: ","Ref\nEquipo/Molde: ","Maquina Parada\nFecha\nTiempo\n","\nLíder Del GAP","Líder Del GAP\nNombre\n","Inicio Intervención\nFecha\nTiempo\n","\nCoadyuvante De Mantenimiento\nNombre\n","Coadyuvante De Mantenimiento\nNombre\n","Final Intervención\nFecha\nTiempo\n","\nCoadyuvante De Mantenimiento\nNombre\n","Coadyuvante De Mantenimiento\nNombre\n","Reinicio De La Máquina\nFecha\nTiempo\n","\nLíder Del GAP","Líder Del GAP\nNombre\n","Descripción De La Avería\n","Accion Realizada Para Arrancar\n","\nCausa Raiz Confirmada"]
        if Engl: SrchVars=EnVars[:]
        else: SrchVars=EsVars[:] 
        
        Usuario=Data_txt(texto, SrchVars[0],1,True,False)
        Uap=Data_txt(texto, SrchVars[1],1,True,False)
        Equipo=Data_txt(texto, SrchVars[2],1,True,False)
        Orden=Data_txt(texto, SrchVars[3],1,True,False)
        EquipoRef=Data_txt(texto, SrchVars[4],1,True,False)
        StopDate=Data_txt(texto,SrchVars[5],1,True,True)
        StopTime=Data_txt(texto, SrchVars[6],1,False,True)
        GapLeaderName=Data_txt(texto, SrchVars[7],1, True,False)
        InterventionDate =Data_txt(texto, SrchVars[8],1,True,True)
        InterventionTime=Data_txt(texto, SrchVars[9],1,False,True)
        IntervenerName=Data_txt(texto, SrchVars[10],1, True,False)
        EndDate=Data_txt(texto, SrchVars[11],1,True,True)
        EndTime=Data_txt(texto, SrchVars[12],2,False,True)
        IntervenerName2=Data_txt(texto, SrchVars[13],2, True,False)
        RestartDate=Data_txt(texto, SrchVars[14],1,True,True)
        RestartTime=Data_txt(texto, SrchVars[15],2,False,True)
        GapLeaderName2=Data_txt(texto, SrchVars[16],2, True,False)
        Descripcion=Data_txt(texto, SrchVars[17],1, True,False)
        
        DTLI= SrchVars[18]
        DTLF= SrchVars[19]
        txtLargo=texto[texto.find(DTLI)+len(DTLI):texto.find(DTLF)]
        txtLargo=Limpieza_Texto(txtLargo,Engl)
        indices = []
        inicio = 0
        while inicio < len(txtLargo):
            inicio = txtLargo.find(";", inicio)
            if inicio == -1:
                break
            indices.append(inicio)
            inicio += 1  
        S_n = len(indices)
        n = int((-1 + math.sqrt(1 + 8 * S_n)) / 2)
        if n==1:
            txtLargo=txtLargo.replace("\n"," ")
            Nombre=txtLargo[:txtLargo.find(":")]#Encontrar Nombre
            txtLargo=txtLargo[0+len(Nombre):]#Eliminar primer nombre
            Descr=[txtLargo] #Hacer lista separando por nombre
            for i in range(len(Descr)): #Limpieza de tareas
                Descr[i]=Descr[i][2:len(Descr[i])-2]
        else:
            txtLargo=txtLargo[indices[len(indices)-1-n]+2:]
            txtLargo=txtLargo.replace("\n"," ")
            Nombre=txtLargo[:txtLargo.find(":")+1]#Encontrar Nombre
            txtLargo=txtLargo[0+len(Nombre):]#Eliminar primer nombre 
            Descr = re.split(regexN(Nombre), txtLargo, flags=re.IGNORECASE)
            Descr = [item.lstrip(' ;').rstrip(' ;') for item in Descr if item.lstrip(' ;').rstrip(' ;')]

        while len(Descr)<len(task):
            Descr.append("---")
        Dict_Tareas={task[i]: Descr[i] for i in range(len(task))}

        doc.close()
        #-----------------------------------------
        #Se genera archivo temporal con tempfile
        # se utiliza para evitar coliciones durante la concurrencia y evitar sobreescribir archivos
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Generar un nuevo PDF con ReportLab
            archivo_salida = temp_file.name
            c = canvas.Canvas(archivo_salida, pagesize=letter)

            width, height = letter

            global pos_y
            global count

            #Definir ruta absoluta para la imagen basada en la ubicacion de la libreria
            image_path = os.path.join(os.path.dirname(__file__), "Faurecia_LOGO.jpeg")
            insertar_imagen(c,image_path,200,100,60,670)


            #---------------------------Texto 1

            # Configurar el texto y fuente
            texto = "Breakdown Log Sheet"
            fuente = "Helvetica-Bold"
            tamano_fuente = 18

            # Registrar y establecer la fuente
            c.setFont(fuente, tamano_fuente)

            # Calcular el ancho del texto
            ancho_texto = pdfmetrics.stringWidth(texto, fuente, tamano_fuente)

            c.drawString(347, 720, texto)
            #Crear tabla

            #----------------------------------texto 2

            variable2 = Usuario
            texto2 = f"User: {variable2}"
            fuente2 = "Helvetica-Bold"
            tamano_fuente2 = 14

            # Registrar y establecer la fuente
            c.setFont(fuente2, tamano_fuente2)

            # Calcular el ancho del texto
            ancho_texto2 = pdfmetrics.stringWidth(texto2, fuente2, tamano_fuente2)

            c.drawString(612-72-ancho_texto2, 700, texto2)


            #------------------------------ texto 3

            variable3 = Uap
            texto3 = f"UAP: {variable3}"
            fuente3 = "Helvetica-Bold"
            tamano_fuente3 = 12

            # Registrar y establecer la fuente
            c.setFont(fuente3, tamano_fuente3)

            # Calcular el ancho del texto
            ancho_texto3 = pdfmetrics.stringWidth(texto3, fuente3, tamano_fuente3)

            c.drawString(75, 660, texto3)
            #------------------------------ texto 4

            variable4 = Equipo
            texto4 = f"Equipment/Tool: {variable4}"
            fuente4 = "Helvetica-Bold"
            tamano_fuente4 = 8

            # Registrar y establecer la fuente
            c.setFont(fuente4, tamano_fuente4)

            # Calcular el ancho del texto
            ancho_texto2 = pdfmetrics.stringWidth(texto4, fuente4, tamano_fuente4)

            c.drawString(75, 620, texto4)

            #------------texto 5

            variable5 = Orden
            texto5 = f"Order: {variable5}"
            fuente5 = "Helvetica-Bold"
            tamano_fuente5 = 12

            # Registrar y establecer la fuente
            c.setFont(fuente5, tamano_fuente5)

            # Calcular el ancho del texto
            ancho_texto5 = pdfmetrics.stringWidth(texto5, fuente5, tamano_fuente5)

            c.drawString(612-75-ancho_texto5, 660, texto5)


            #-- texto 6

            variable6 = EquipoRef
            texto6 = f"Equip/Tool ref: {variable6}"
            fuente6 = "Helvetica-Bold"
            tamano_fuente6 = 8

            # Registrar y establecer la fuente
            c.setFont(fuente6, tamano_fuente6)

            # Calcular el ancho del texto
            ancho_texto6 = pdfmetrics.stringWidth(texto6, fuente6, tamano_fuente6)

            c.drawString(612-75-ancho_texto6, 620, texto6)

            #------------------------ Primeras 2 tablas

            colWidths=115.2 #Grosor de las columnas de la tabla
            data = [["Machine Stopped", ""], ["Date", "Time"], [StopDate, StopTime]] 

            table = Table(data, colWidths)

            # Configurar estilo de la tabla
            table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            #Ancho y alto de la tabla
            table_width, table_height = table.wrap(0,0)

            #Posicion de la tabla
            x = 75
            y = 580 - table_height
            table.wrapOn(c, x, y)
            table.drawOn(c, x,y)
            #----------

            colWidths2=110*2-20#Grosor de las columnas de la tabla
            data2 = [["Gap Leader"], ["Name"], [GapLeaderName]] 

            table2 = Table(data2, colWidths2)

            # Configurar estilo de la tabla #koi
            table2.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width2, table_height2 = table2.wrap(0,0)

            #Posicion de la tabla
            x2 = 381-75 + 30
            y2 = 580 - table_height2
            table2.wrapOn(c, x2, y2)
            table2.drawOn(c, x2,y2)


            # -- Siguiente hilera de tablas 

            colWidths3=115.2#Grosor de las columnas de la tabla
            data3 = [["Start Intervention", ""], ["Date", "Time"], [InterventionDate, InterventionTime]] 

            table3 = Table(data3, colWidths3)

            # Configurar estilo de la tabla
            table3.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width3, table_height3 = table3.wrap(0,0)

            #Posicion de la tabla
            x3 = 75
            y3 = 550 - table_height - table_height3
            table3.wrapOn(c, x3, y3)
            table3.drawOn(c, x3,y3)
            #----------

            colWidths4=115.2*2 -30#Grosor de las columnas de la tabla
            data4 = [["Maintenance Intervener"], ["Name"], [IntervenerName]]

            table4 = Table(data4, colWidths4)

            # Configurar estilo de la tabla
            table4.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width4, table_height4 = table4.wrap(0,0)

            #Posicion de la tabla
            x4 = 381-75 + 30
            y4 = y3
            table4.wrapOn(c, x4, y4)
            table4.drawOn(c, x4,y4)

            #----------------------------- TERCERA HILERA

            colWidths5=115.2#Grosor de las columnas de la tabla
            data5 = [["End intervention", ""], ["Date", "Time"], [EndDate, EndTime]] 

            table5 = Table(data5, colWidths5)

            # Configurar estilo de la tabla
            table5.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width5, table_height5 = table5.wrap(0,0)

            #Posicion de la tabla
            x5 = 75
            y5 = 530 - table_height - table_height3 - table_height5
            table5.wrapOn(c, x5, y5)
            table5.drawOn(c, x5,y5)
            #----------

            colWidth6=115.2*2 -30#Grosor de las columnas de la tabla
            data6 = [["Maintenance Intervener"], ["Name"], [IntervenerName2]]

            table6 = Table(data6, colWidth6)

            # Configurar estilo de la tabla
            table6.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width6, table_height6 = table6.wrap(0,0)

            #Posicion de la tabla
            x6 = 381-75 + 30
            y6 = y5
            table6.wrapOn(c, x6, y6)
            table6.drawOn(c, x6,y6)

            # ------------------------------------- Cuarta hilera

            colWidths7=115.2#Grosor de las columnas de la tabla
            data7 = [["Machine Restart", ""], ["Date", "Time"], [RestartDate, RestartTime]] 

            table7 = Table(data7, colWidths7)

            # Configurar estilo de la tabla
            table7.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width7, table_height7 = table7.wrap(0,0)

            #Posicion de la tabla
            x7 = 75
            y7 = 510 - table_height - table_height3 - table_height5 -table_height7
            table7.wrapOn(c, x7, y7)
            table7.drawOn(c, x7,y7)
            #----------

            colWidth8=115.2*2 -30#Grosor de las columnas de la tabla
            data8 = [["Gap Leader"], ["Name"], [GapLeaderName2]]

            table8 = Table(data8, colWidth8)

            # Configurar estilo de la tabla
            table8.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width8, table_height8 = table8.wrap(0,0)

            #Posicion de la tabla
            x8 = 381-75 + 30
            y8 = y7
            table8.wrapOn(c, x8, y8)
            table8.drawOn(c, x8,y8)


            # Configurar el texto y fuente
            texto7 = "!!!Respect safety rules!!"
            fuente7 = "Helvetica-Bold"
            tamano_fuente7 = 12

            # Registrar y establecer la fuente
            c.setFont(fuente7, tamano_fuente7)

            # Calcular el ancho del texto
            ancho_texto7 = pdfmetrics.stringWidth(texto7, fuente7, tamano_fuente7)

            c.drawString(((612)-ancho_texto7)/2, 254, texto7)

            # Configurar el texto y fuente
            texto8 = "!!!My PI is in place, the zone is secured, I wear the correct PPE!!"
            fuente8 = "Helvetica-Bold"
            tamano_fuente8 = 12

            # Registrar y establecer la fuente
            c.setFont(fuente8, tamano_fuente8)

            # Calcular el ancho del texto
            ancho_texto8 = pdfmetrics.stringWidth(texto8, fuente8, tamano_fuente8)

            c.drawString(((612)-ancho_texto8)/2, 234, texto8)


            ###----------- tabla 9

            colWidth9=522-60#Grosor de las columnas de la tabla
            #data9 = [["Description of the breakdown"], ["Columna"], ["-"]]
            data9 = [["Description of the breakdown"], [Descripcion]]

            table9 = Table(data9, colWidth9)

            # Configurar estilo de la tabla
            table9.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))

            table_width9, table_height9 = table9.wrap(0,0)

            #Posicion de la tabla
            x9 = 75
            y9 = 214 - table_height9
            table9.wrapOn(c, x9, y9)
            table9.drawOn(c, x9,y9)

            #Agregar otra hoja
            c.showPage()

            #global pos_y
            pos_y = height - 75
            count = 1
            def insertar_tabla(a,b):
                global pos_y
                global count
                colWidth=(462)/2#Grosor de las columnas de la tabla
                data = [[f"Tarea {count}", f"Comentario {count}"], [a,b]]

                table = Table(data, colWidth)

                # Configurar estilo de la tabla
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                    ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
                ]))



                table_width, table_height = table.wrap(0,0)

                if pos_y-table_height<75:
                    c.showPage()
                    pos_y = height - 75

                #Posicion de la tabla
                x = 75
                y = pos_y - table_height
            
                table.wrapOn(c, x, y)
                table.drawOn(c, x,y)

                pos_y = y - 20
                count += 1


            for i in Dict_Tareas:
                insertar_tabla(ajustar_texto(i,230), ajustar_texto(Dict_Tareas[i],230))

            # Finalizar el PDF
            c.showPage()
            c.save()
        return archivo_salida

    except Exception as e:
        if 'archivo_salida' in locals() and os.path.exists(archivo_salida):
            os.remove(archivo_salida)  # Limpia si hay error
        raise Exception(f"Error al procesar archivos para auditorías: {e}")

# Función para guardar el nuevo PDF generado
# **************** REDUNDANTE EN SERVIDOR PUES SEGUARDA DIRECTAMENTE DESDE EL FRONT CON JS ***********
"""
def guardar_pdf():
    global archivo_salida

    if not archivo_salida:
        messagebox.showwarning("Advertencia", "Primero procese los archivos para generar un PDF.")
        return

    destino = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
    if destino:
        try:
            with open(archivo_salida, "rb") as src:
                with open(destino, "wb") as dst:
                    dst.write(src.read())
            messagebox.showinfo("Éxito", f"Archivo guardado en: {destino}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
"""
# ************************************ DESCOMENTAR EN OTROS CASOS **************************************


def procesar_archivos_2(archivo_pdf, archivo_excel):
   
    try:
        # Leer los bytes del PDF desde el objeto FileStorage
        pdf_bytes = archivo_pdf.read()
        # Abrir el PDF desde los bytes en memoria usando BytesIO
        doc = pymupdf.open(stream=BytesIO(pdf_bytes), filetype="pdf")
 
        # Procesar el archivo Excel
        df = pd.read_csv(archivo_excel)
 
        text_buffer = StringIO()
        for page in doc:
            text = page.get_text()
            text_buffer.write(text)
            text_buffer.write('\f')  # Separador de página (equivalente a bytes((12,)))
        texto = text_buffer.getvalue()
        text_buffer.close()
       
        task=[]
        for t in df.DS_WORK_OPERA:
            task.append(t)
       
        Engl="Breakdown Log Sheet" in texto
        EnVars=["User: ","UAP: ","Equipment/Tool: ","Order: ","Equip/Tool ref: ","Machine Stopped\nDate\nTime\n","\nGap Leader","Gap Leader\nName\n","Start Intervention\nDate\nTime\n","\nMaintenance Intervener\nName\n","Maintenance Intervener\nName\n","End Intervention\nDate\nTime\n","\nMaintenance Intervener\nName\n","Maintenance Intervener\nName\n","Machine Restart\nDate\nTime\n","\nGap Leader","Gap Leader\nName\n","Description of the Breakdown\n","Actions Done to Restart\n","\nRoot Cause Confirmed"]
        EsVars=["User: ","UAP: ","Equipo/Molde: ","Orden: ","Ref\nEquipo/Molde: ","Maquina Parada\nFecha\nTiempo\n","\nLíder Del GAP","Líder Del GAP\nNombre\n","Inicio Intervención\nFecha\nTiempo\n","\nCoadyuvante De Mantenimiento\nNombre\n","Coadyuvante De Mantenimiento\nNombre\n","Final Intervención\nFecha\nTiempo\n","\nCoadyuvante De Mantenimiento\nNombre\n","Coadyuvante De Mantenimiento\nNombre\n","Reinicio De La Máquina\nFecha\nTiempo\n","\nLíder Del GAP","Líder Del GAP\nNombre\n","Descripción De La Avería\n","Accion Realizada Para Arrancar\n","\nCausa Raiz Confirmada"]
        if Engl: SrchVars=EnVars[:]
        else: SrchVars=EsVars[:] 
        
        Usuario=Data_txt(texto, SrchVars[0],1,True,False)
        Uap=Data_txt(texto, SrchVars[1],1,True,False)
        Equipo=Data_txt(texto, SrchVars[2],1,True,False)
        Orden=Data_txt(texto, SrchVars[3],1,True,False)
        EquipoRef=Data_txt(texto, SrchVars[4],1,True,False)
        StopDate=Data_txt(texto,SrchVars[5],1,True,True)
        StopTime=Data_txt(texto, SrchVars[6],1,False,True)
        GapLeaderName=Data_txt(texto, SrchVars[7],1, True,False)
        InterventionDate =Data_txt(texto, SrchVars[8],1,True,True)
        InterventionTime=Data_txt(texto, SrchVars[9],1,False,True)
        IntervenerName=Data_txt(texto, SrchVars[10],1, True,False)
        EndDate=Data_txt(texto, SrchVars[11],1,True,True)
        EndTime=Data_txt(texto, SrchVars[12],2,False,True)
        IntervenerName2=Data_txt(texto, SrchVars[13],2, True,False)
        RestartDate=Data_txt(texto, SrchVars[14],1,True,True)
        RestartTime=Data_txt(texto, SrchVars[15],2,False,True)
        GapLeaderName2=Data_txt(texto, SrchVars[16],2, True,False)
        Descripcion=Data_txt(texto, SrchVars[17],1, True,False)
        
        DTLI= SrchVars[18]
        DTLF= SrchVars[19]
        txtLargo=texto[texto.find(DTLI)+len(DTLI):texto.find(DTLF)]
        txtLargo=Limpieza_Texto(txtLargo,Engl)
        indices = []
        inicio = 0
        while inicio < len(txtLargo):
            inicio = txtLargo.find(";", inicio)
            if inicio == -1:
                break
            indices.append(inicio)
            inicio += 1  
        S_n = len(indices)
        n = int((-1 + math.sqrt(1 + 8 * S_n)) / 2)
        if n==1:
            txtLargo=txtLargo.replace("\n"," ")
            Nombre=txtLargo[:txtLargo.find(":")]#Encontrar Nombre
            txtLargo=txtLargo[0+len(Nombre):]#Eliminar primer nombre
            Descr=[txtLargo] #Hacer lista separando por nombre
            for i in range(len(Descr)): #Limpieza de tareas
                Descr[i]=Descr[i][2:len(Descr[i])-2]
        else:
            txtLargo=txtLargo[indices[len(indices)-1-n]+2:]
            txtLargo=txtLargo.replace("\n"," ")
            Nombre=txtLargo[:txtLargo.find(":")+1]#Encontrar Nombre
            txtLargo=txtLargo[0+len(Nombre):]#Eliminar primer nombre 
            Descr = re.split(regexN(Nombre), txtLargo, flags=re.IGNORECASE)
            Descr = [item.lstrip(' ;').rstrip(' ;') for item in Descr if item.lstrip(' ;').rstrip(' ;')]

        while len(Descr)<len(task):
            Descr.append("---")
        Dict_Tareas={task[i]: Descr[i] for i in range(len(task))}
 
        HOURS = []
 
        for i in df.QT_HOURS_SUM:
            HOURS.append(str(decimal_a_horas(i)))
 
        nuevo_diccionario = {}
        for i, clave in enumerate(Dict_Tareas):
            nuevo_diccionario[clave] = [Dict_Tareas[clave], HOURS[i]]
        doc.close()
        #-----------------------------------------
        # Se genera un archivo temporal con tempfile para evitar colisiones durante la concurrencia
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Generar un nuevo PDF con ReportLab
            archivo_salida = temp_file.name
            c = canvas.Canvas(archivo_salida, pagesize=letter)
 
            width, height = letter
 
            global pos_y
            global count
 
            #Definir ruta absoluta para la imagen basada en la ubicacion de la libreria
            image_path = os.path.join(os.path.dirname(__file__), "Faurecia_LOGO.jpeg")
            insertar_imagen(c,image_path,200,100,60,670)
 
 
            #---------------------------Texto 1
 
            # Configurar el texto y fuente
            texto = "Breakdown Log Sheet"
            fuente = "Helvetica-Bold"
            tamano_fuente = 18
 
            # Registrar y establecer la fuente
            c.setFont(fuente, tamano_fuente)
 
            # Calcular el ancho del texto
            ancho_texto = pdfmetrics.stringWidth(texto, fuente, tamano_fuente)
 
            c.drawString(347, 720, texto)
            #Crear tabla
 
            #----------------------------------texto 2
 
            variable2 = Usuario
            texto2 = f"User: {variable2}"
            fuente2 = "Helvetica-Bold"
            tamano_fuente2 = 14
 
            # Registrar y establecer la fuente
            c.setFont(fuente2, tamano_fuente2)
 
            # Calcular el ancho del texto
            ancho_texto2 = pdfmetrics.stringWidth(texto2, fuente2, tamano_fuente2)
 
            c.drawString(612-72-ancho_texto2, 700, texto2)
 
 
            #------------------------------ texto 3
 
            variable3 = Uap
            texto3 = f"UAP: {variable3}"
            fuente3 = "Helvetica-Bold"
            tamano_fuente3 = 12
 
            # Registrar y establecer la fuente
            c.setFont(fuente3, tamano_fuente3)
 
            # Calcular el ancho del texto
            ancho_texto3 = pdfmetrics.stringWidth(texto3, fuente3, tamano_fuente3)
 
            c.drawString(75, 660, texto3)
            #------------------------------ texto 4
 
            variable4 = Equipo
            texto4 = f"Equipment/Tool: {variable4}"
            fuente4 = "Helvetica-Bold"
            tamano_fuente4 = 8
 
            # Registrar y establecer la fuente
            c.setFont(fuente4, tamano_fuente4)
 
            # Calcular el ancho del texto
            ancho_texto2 = pdfmetrics.stringWidth(texto4, fuente4, tamano_fuente4)
 
            c.drawString(75, 620, texto4)
 
            #------------texto 5
 
            variable5 = Orden
            texto5 = f"Order: {variable5}"
            fuente5 = "Helvetica-Bold"
            tamano_fuente5 = 12
 
            # Registrar y establecer la fuente
            c.setFont(fuente5, tamano_fuente5)
 
            # Calcular el ancho del texto
            ancho_texto5 = pdfmetrics.stringWidth(texto5, fuente5, tamano_fuente5)
 
            c.drawString(612-75-ancho_texto5, 660, texto5)
 
 
            #-- texto 6
 
            variable6 = EquipoRef
            texto6 = f"Equip/Tool ref: {variable6}"
            fuente6 = "Helvetica-Bold"
            tamano_fuente6 = 8
 
            # Registrar y establecer la fuente
            c.setFont(fuente6, tamano_fuente6)
 
            # Calcular el ancho del texto
            ancho_texto6 = pdfmetrics.stringWidth(texto6, fuente6, tamano_fuente6)
 
            c.drawString(612-75-ancho_texto6, 620, texto6)
 
            #------------------------ Primeras 2 tablas
 
            colWidths=115.2 #Grosor de las columnas de la tabla
            data = [["Machine Stopped", ""], ["Date", "Time"], [StopDate, StopTime]]
 
            table = Table(data, colWidths)
 
            # Configurar estilo de la tabla
            table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            #Ancho y alto de la tabla
            table_width, table_height = table.wrap(0,0)
 
            #Posicion de la tabla
            x = 75
            y = 580 - table_height
            table.wrapOn(c, x, y)
            table.drawOn(c, x,y)
            #----------
 
            colWidths2=110*2-20#Grosor de las columnas de la tabla
            data2 = [["Gap Leader"], ["Name"], [GapLeaderName]]
 
            table2 = Table(data2, colWidths2)
 
            # Configurar estilo de la tabla #koi
            table2.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width2, table_height2 = table2.wrap(0,0)
 
            #Posicion de la tabla
            x2 = 381-75 + 30
            y2 = 580 - table_height2
            table2.wrapOn(c, x2, y2)
            table2.drawOn(c, x2,y2)
 
 
            # -- Siguiente hilera de tablas
 
            colWidths3=115.2#Grosor de las columnas de la tabla
            data3 = [["Start Intervention", ""], ["Date", "Time"], [InterventionDate, InterventionTime]]
 
            table3 = Table(data3, colWidths3)
 
            # Configurar estilo de la tabla
            table3.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width3, table_height3 = table3.wrap(0,0)
 
            #Posicion de la tabla
            x3 = 75
            y3 = 550 - table_height - table_height3
            table3.wrapOn(c, x3, y3)
            table3.drawOn(c, x3,y3)
            #----------
 
            colWidths4=115.2*2 -30#Grosor de las columnas de la tabla
            data4 = [["Maintenance Intervener"], ["Name"], [IntervenerName]]
 
            table4 = Table(data4, colWidths4)
 
            # Configurar estilo de la tabla
            table4.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width4, table_height4 = table4.wrap(0,0)
 
            #Posicion de la tabla
            x4 = 381-75 + 30
            y4 = y3
            table4.wrapOn(c, x4, y4)
            table4.drawOn(c, x4,y4)
 
            #----------------------------- TERCERA HILERA
 
            colWidths5=115.2#Grosor de las columnas de la tabla
            data5 = [["End intervention", ""], ["Date", "Time"], [EndDate, EndTime]]
 
            table5 = Table(data5, colWidths5)
 
            # Configurar estilo de la tabla
            table5.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width5, table_height5 = table5.wrap(0,0)
 
            #Posicion de la tabla
            x5 = 75
            y5 = 530 - table_height - table_height3 - table_height5
            table5.wrapOn(c, x5, y5)
            table5.drawOn(c, x5,y5)
            #----------
 
            colWidth6=115.2*2 -30#Grosor de las columnas de la tabla
            data6 = [["Maintenance Intervener"], ["Name"], [IntervenerName2]]
 
            table6 = Table(data6, colWidth6)
 
            # Configurar estilo de la tabla
            table6.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width6, table_height6 = table6.wrap(0,0)
 
            #Posicion de la tabla
            x6 = 381-75 + 30
            y6 = y5
            table6.wrapOn(c, x6, y6)
            table6.drawOn(c, x6,y6)
 
            # ------------------------------------- Cuarta hilera
 
            colWidths7=115.2#Grosor de las columnas de la tabla
            data7 = [["Machine Restart", ""], ["Date", "Time"], [RestartDate, RestartTime]]
 
            table7 = Table(data7, colWidths7)
 
            # Configurar estilo de la tabla
            table7.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width7, table_height7 = table7.wrap(0,0)
 
            #Posicion de la tabla
            x7 = 75
            y7 = 510 - table_height - table_height3 - table_height5 -table_height7
            table7.wrapOn(c, x7, y7)
            table7.drawOn(c, x7,y7)
            #----------
 
            colWidth8=115.2*2 -30#Grosor de las columnas de la tabla
            data8 = [["Gap Leader"], ["Name"], [GapLeaderName2]]
 
            table8 = Table(data8, colWidth8)
 
            # Configurar estilo de la tabla
            table8.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width8, table_height8 = table8.wrap(0,0)
 
            #Posicion de la tabla
            x8 = 381-75 + 30
            y8 = y7
            table8.wrapOn(c, x8, y8)
            table8.drawOn(c, x8,y8)
 
 
            # Configurar el texto y fuente
            texto7 = "!!!Respect safety rules!!"
            fuente7 = "Helvetica-Bold"
            tamano_fuente7 = 12
 
            # Registrar y establecer la fuente
            c.setFont(fuente7, tamano_fuente7)
 
            # Calcular el ancho del texto
            ancho_texto7 = pdfmetrics.stringWidth(texto7, fuente7, tamano_fuente7)
 
            c.drawString(((612)-ancho_texto7)/2, 254, texto7)
 
            # Configurar el texto y fuente
            texto8 = "!!!My PI is in place, the zone is secured, I wear the correct PPE!!"
            fuente8 = "Helvetica-Bold"
            tamano_fuente8 = 12
 
            # Registrar y establecer la fuente
            c.setFont(fuente8, tamano_fuente8)
 
            # Calcular el ancho del texto
            ancho_texto8 = pdfmetrics.stringWidth(texto8, fuente8, tamano_fuente8)
 
            c.drawString(((612)-ancho_texto8)/2, 234, texto8)
 
 
            ###----------- tabla 9
 
            colWidth9=522-60#Grosor de las columnas de la tabla
            #data9 = [["Description of the breakdown"], ["Columna"], ["-"]]
            data9 = [["Description of the breakdown"], [Descripcion]]
 
            table9 = Table(data9, colWidth9)
 
            # Configurar estilo de la tabla
            table9.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 1), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
            ]))
 
            table_width9, table_height9 = table9.wrap(0,0)
 
            #Posicion de la tabla
            x9 = 75
            y9 = 214 - table_height9
            table9.wrapOn(c, x9, y9)
            table9.drawOn(c, x9,y9)
 
            #Agregar otra hoja
            c.showPage()
 
            #global pos_y
            pos_y = height - 75
            count = 1
            def insertar_tabla(a,b,hora):
                global pos_y
                global count
                colWidth=(462)/3#Grosor de las columnas de la tabla
                data = [[f"Tarea {count}", f"Comentario {count}", f"Tiempo"], [a,b, hora]]
 
                table = Table(data, colWidth)
 
                # Configurar estilo de la tabla
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0024D3")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor("#BDFFF1")),
                    ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Asegura que el texto se mantenga centrado verticalmente
                ]))
 
 
 
                table_width, table_height = table.wrap(0,0)
 
                if pos_y-table_height<75:
                    c.showPage()
                    pos_y = height - 75
 
                #Posicion de la tabla
                x = 75
                y = pos_y - table_height
           
                table.wrapOn(c, x, y)
                table.drawOn(c, x,y)
 
                pos_y = y - 20
                count += 1
 
 
            for i in nuevo_diccionario:
                insertar_tabla(ajustar_texto(i,153),
                            ajustar_texto(nuevo_diccionario[i][0],153),
                            ajustar_texto(nuevo_diccionario[i][1],153))
 
 
 
            # Finalizar el PDF
            c.showPage()
            c.save()
        return archivo_salida
    except Exception as e:
        if 'archivo_salida' in locals() and os.path.exists(archivo_salida):
            os.remove(archivo_salida)  # Limpia si hay error
        raise Exception(f"Error al procesar archivos para coordinadores: {e}")