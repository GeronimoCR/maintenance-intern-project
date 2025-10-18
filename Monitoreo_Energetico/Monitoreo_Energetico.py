from flask import Blueprint, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import smtplib
from email.mime.text import MIMEText

monitoreo_bp = Blueprint('monitoreo', __name__, template_folder='../Templates', static_folder='../static')
CORS(monitoreo_bp)

# CONFIGURACION CARPETA DE UPLOADS
UPLOAD_FOLDER = os.path.join('Uploads', 'Monitoreo')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Crear la carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_filemap(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg'}







# FUNCION PARA OBTENER EL COLOR DE CADA MAQUINA
def get_color(consumo: float, Enc_NProd: float = 200, Enc_Prod: float = 400, Alert: float = 600) -> str:
    if pd.isna(consumo) or consumo == "NO DATA":
        return "black"
    if consumo > Alert:
        return "red"
    elif consumo > Enc_Prod:
        return "limegreen"
    elif consumo > Enc_NProd:
        return "blue"
    else:
        return "#795c32"

# FUNCION PARA OBTENER EL STATUS DE CADA MAQUINA
def get_status(color):
    status_map = {
        "black": "Sin registros (posible fallo en medición)",
        "red": "Alerta consumo excesivo",
        "limegreen": "Encendido produciendo",
        "blue": "Encendido sin producir",
        "#795c32": "Apagada"
    }
    return status_map.get(color, "Estado desconocido")


# FUNCION PARA GENERAR EL CUERPO DEL CORREO
def generate_email_body(data, last_date):
    try:
        # Agrupar máquinas por área
        areas = {}
        for item in data:
            area = item.get("area", "SIN_AREA")
            if not area:
                area = "SIN_AREA"
            if area not in areas:
                areas[area] = []
            status = get_status(item["color"])
            maquina = item.get("maquina", "SIN_NOMBRE")
            consumo = item.get("consumo")
            # Limpiar el estado para evitar caracteres no imprimibles
            status = ''.join(c for c in str(status) if c.isprintable())
            areas[area].append(f"- {maquina}: {status} - {consumo} KWh")
        
        # Construir el cuerpo del correo
        email_body = f"Resumen Consumo Energético - {last_date}\n\n"
        for area in sorted(areas.keys()):  # Ordenar áreas alfabéticamente
            email_body += f"{area}\n"
            for maquina in sorted(areas[area]):  # Ordenar máquinas alfabéticamente
                email_body += f"{maquina}\n"
            email_body += "\n"  # Espacio entre áreas
        return email_body
    except Exception as e:
        print(f"Error al generar el cuerpo del correo: {str(e)}")
        raise Exception(f"Error al generar el cuerpo del correo: {str(e)}")


# FUNCIÓN PARA ENVIAR EL CORREO
def send_email(subject, body, to_email, from_email, smtp_server, smtp_port, app_password):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_email)

    try:
        # Conectar al servidor SMTP de Gmail
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Iniciar conexión segura con TLS
        server.login(from_email, app_password)  # Autenticar con correo y contraseña de aplicación
        server.sendmail(from_email, to_email, msg.as_string())  # Enviar a todos los destinatarios
        server.quit()
        print("Correo enviado exitosamente")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

# FUNCION PARA PROCESAR EXCEL SUBIDO DE METRON Y DEVOLVER LA INFORMACION PARA MAPAS
def process_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        df['Date'] = pd.to_datetime(df["Date"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
        last_date = df['Date'].max()
        last_date_str = last_date.strftime('%d/%m/%Y %H:%M:%S') if pd.notnull(last_date) else "No date available"

        Maquinas = list(df.Title.unique())
        columnas = ["Maquina", "Consumo"]
        dfR = pd.DataFrame(columns=columnas)
        for maquina in Maquinas:
            dfmaquina = df[df["Title"] == maquina]
            dfmaquina = dfmaquina.sort_values(by="Date", ascending=False)
            Dato_reciente = dfmaquina.iloc[0]
            Ma = Dato_reciente["Title"]
            Co = Dato_reciente["Value"]
            Maquina_Consumo = [Ma, Co]
            dfR.loc[len(dfR)] = Maquina_Consumo
        dfR['Consumo'] = dfR['Consumo'].replace(np.nan, 0)
        data = dfR.to_dict(orient="records")
        
        data_dict = {item["Maquina"]: item["Consumo"] for item in data}
        
        # LEER BASES DE DATOS
        # Diccionario para Nave1 
        coordenadas1 = pd.read_excel(os.path.join(UPLOAD_FOLDER, 'coordenadas1.xlsx')).set_index('Nombre').to_dict(orient='index')
        # Diccionario para Nave2 
        coordenadas2 = pd.read_excel(os.path.join(UPLOAD_FOLDER, 'coordenadas2.xlsx')).set_index('Nombre').to_dict(orient='index')
        result = []
        for zona, coordenadas in [("Nave1", coordenadas1), ("Nave2", coordenadas2)]:
            for maquina in coordenadas:
                if maquina in data_dict:
                    consumo = data_dict[maquina]
                    limite_ENP = coordenadas[maquina].get("Enc_NProd", 200)
                    limite_EP = coordenadas[maquina].get("Enc_Prod", 400)
                    limite_AL = coordenadas[maquina].get("Alert", 600)
                    color = get_color(consumo, limite_ENP, limite_EP, limite_AL)
                    radio = coordenadas[maquina].get("Rad", 5)
                else:
                    consumo = "NO DATA"
                    color = "black"
                    radio = coordenadas[maquina].get("Rad", 5)
                
                coords = coordenadas[maquina]
                result.append({
                    "maquina": maquina,
                    "consumo": consumo,
                    "color": color,
                    "radio": radio,
                    "x": coords["y"],
                    "y": coords["x"],
                    "zona": zona,
                    "area": coords.get("Area", "SIN_AREA")
                })
        
        return {
            "data": result,
            "last_date": last_date_str
        }
    except Exception as e:
        raise Exception(f"Error procesando el archivo: {str(e)}")


# FUNCION PARA PROCESAR EXCEL SUBIDO DE METRON Y DEVOLVER LA INFORMACION PARA **** TABLA ****
def process_excel_Tbl(file_path):
    try:
        df = pd.read_excel(file_path)
        df['Date'] = pd.to_datetime(df["Date"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
        last_date = df['Date'].max()
        last_date_str = last_date.strftime('%d/%m/%Y %H:%M:%S') if pd.notnull(last_date) else "No date available"

        Maquinas = list(df.Title.unique())
        columnas = ["Maquina", "Consumo"]
        dfR = pd.DataFrame(columns=columnas)
        for maquina in Maquinas:
            dfmaquina = df[df["Title"] == maquina]
            dfmaquina = dfmaquina.sort_values(by="Date", ascending=False)
            Dato_reciente = dfmaquina.iloc[0]
            Ma = Dato_reciente["Title"]
            Co = Dato_reciente["Value"]
            Maquina_Consumo = [Ma, Co]
            dfR.loc[len(dfR)] = Maquina_Consumo
        dfR['Consumo'] = dfR['Consumo'].replace(np.nan, 0)
        data = dfR.to_dict(orient="records")
        
        data_dict = {item["Maquina"]: item["Consumo"] for item in data}
        
        # LEER BASES DE DATOS
        # Diccionario para Nave1 
        coordenadas1 = pd.read_excel(os.path.join(UPLOAD_FOLDER, 'coordenadas1.xlsx')).set_index('Nombre').to_dict(orient='index')
        # Diccionario para Nave2 
        coordenadas2 = pd.read_excel(os.path.join(UPLOAD_FOLDER, 'coordenadas2.xlsx')).set_index('Nombre').to_dict(orient='index')
        result = []
        for coordenadas in [coordenadas1, coordenadas2]:
            for maquina in coordenadas:
                if maquina in data_dict:
                    consumo = data_dict[maquina]
                    limite_ENP = coordenadas[maquina].get("Enc_NProd", 200)
                    limite_EP = coordenadas[maquina].get("Enc_Prod", 400)
                    limite_AL = coordenadas[maquina].get("Alert", 600)
                    color = get_color(consumo, limite_ENP, limite_EP, limite_AL)
                else:
                    consumo = "NO DATA"
                    color = "black"
                status =get_status(color)
                
                coords = coordenadas[maquina]
                result.append({
                    "maquina": maquina,
                    "status": status,
                    "consumo": consumo,
                    "area": coords.get("Area", "SIN_AREA")
                })
        
        return {
            "data": result,
            "last_date": last_date_str
        }
    except Exception as e:
        raise Exception(f"Error procesando el archivo: {str(e)}")
    
# FUNCION PARA GENERAR DATOS DE TABLA
def generate_table(data, last_date):
    # Agrupar máquinas por área
    areas = {}
    for item in data:
        area = item.get("area", "SIN_AREA")
        if not area:
            area = "SIN_AREA"
        if area not in areas:
            areas[area] = []
        status = item.get ("status")
        maquina = item.get("maquina", "SIN_NOMBRE")
        consumo = item.get("consumo")
        areas[area].append({"maquina": maquina, "status": status, "consumo": consumo})
        table_info=[last_date ,areas]
    return table_info

# ++++++++++++++++++++++++++ RUTAS TEMPLATES DE MAPAS Y PAGINA PRINCIPAL DE MAPAS ++++++++++++++++++++
@monitoreo_bp.route('/nave1')
def nave1():
    return render_template('Monitoreo/MapNave1.html')

@monitoreo_bp.route('/nave2')
def nave2():
    return render_template('Monitoreo/MapNave2.html')

@monitoreo_bp.route('/mapa_principal')
def mapa_principal():
    return render_template('Monitoreo/Mapa_principal.html')


# ++++++++++++++++++ RUTAS TEMPLATES EDICION DE OBJETOS +++++++++++++++++++++++++++

@monitoreo_bp.route('/EditObj', methods=['GET'])
def EditObj():
    return render_template('Monitoreo/EditObj.html')

@monitoreo_bp.route('/AddObj', methods=['GET'])
def AddObj():
    return render_template('Monitoreo/AddObj.html')

@monitoreo_bp.route('/DelObj')
def DelObj():
    return render_template('Monitoreo/DelObj.html')

@monitoreo_bp.route('/Layout')
def Layout():
    return render_template('Monitoreo/Layout.html')

@monitoreo_bp.route('/Correos')
def Correos():
    return render_template('Monitoreo/Correos.html')


# +++++++++++++++++++++++++  RUTAS DE MAPAS Y MAPA PRNCIAL (DATOS) ++++++++++++++++++++++++

@monitoreo_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = 'Data_Act.xlsx'
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            result = process_excel(file_path)
            email_body = generate_email_body(result["data"], result["last_date"])
            # CONFIGURACION DE ENVIO DE CORREO GMAIL (PROTOCOLO, REMITENTE, Y DESTINATARIO)
            EXCEL_Mails = os.path.join(UPLOAD_FOLDER, 'Correos.xlsx') #Archivo de correos lista
            mail_list=list(pd.read_excel(EXCEL_Mails).Correos.unique())
            SMTP_SERVER = "smtp.gmail.com"  # Servidor SMTP de Gmail
            SMTP_PORT = 587  # Puerto para TLS
            FROM_EMAIL = "energy.reports01@gmail.com"  #Correo de envio
            APP_PASSWORD = "manu tuld vyti oynr" 
            TO_EMAIL = mail_list #Lista de correos a enviar
            send_email(
                subject=f"Resumen Consumo Energético - {result['last_date']}",
                body=email_body,
                to_email=TO_EMAIL,
                from_email=FROM_EMAIL,
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT,
                app_password=APP_PASSWORD
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file format"}), 400


@monitoreo_bp.route('/get_data', methods=['GET'])
def get_data():
    file_path = os.path.join(UPLOAD_FOLDER, 'Data_Act.xlsx')
    if os.path.exists(file_path):
        try:
            result = process_excel(file_path)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No data available"}), 404
    

@monitoreo_bp.route('/energy_tables', methods=['GET'])
def get_energy_tables():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'Data_Act.xlsx')
        if not os.path.exists(file_path):
            return jsonify({"error": "No hay archivo Data_Act.xlsx cargado"}), 400
        
        # Procesar el archivo y generar los datos de la tabla
        processed_data = process_excel_Tbl(file_path)
        table_info = generate_table(processed_data['data'], processed_data['last_date'])
        
        # Formatear la respuesta
        response = {
            "last_date": table_info[0],
            "areas": table_info[1]
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"Error al procesar los datos: {str(e)}"}), 500


# ***************************** RUTAS EDIT OBJECT *********************************
@monitoreo_bp.route('/get_object_data', methods=['POST'])
def get_object_data():
    try:
        data = request.json
        nombre = data.get('nombre')
        nave = data.get('nave')
        
        excel_file = os.path.join(UPLOAD_FOLDER, f'coordenadas{nave}.xlsx')
        if not os.path.exists(excel_file):
            return jsonify({'error': 'Archivo no encontrado'}), 404
            
        # Leer el Excel y convertir tipos
        df = pd.read_excel(excel_file)
        # Convertir columnas numéricas a float
        numeric_cols = ['x', 'y', 'Enc_NProd', 'Enc_Prod', 'Alert', 'Rad']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
        df['Area'] = df['Area'].astype(str)
        
        if nombre not in df['Nombre'].values:
            return jsonify({'error': f'Equipo no encontrado en Nave {nave}'}), 404
            
        row = df[df['Nombre'] == nombre].iloc[0]
        response = {
            'x': row['x'],
            'y': row['y'],
            'Enc_NProd': row['Enc_NProd'],
            'Enc_Prod': row['Enc_Prod'],
            'Alert': row['Alert'],
            'Rad': row['Rad'],
            'Area': row['Area']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoreo_bp.route('/update_object', methods=['POST'])
def update_object():
    try:
        data = request.json
        nombre = data.get('nombre')
        nave = data.get('nave')
        updates = data.get('updates')
        
        excel_file = os.path.join(UPLOAD_FOLDER, f'coordenadas{nave}.xlsx')
        if not os.path.exists(excel_file):
            return jsonify({'error': 'Archivo no encontrado'}), 404
            
        df = pd.read_excel(excel_file)
        if nombre not in df['Nombre'].values:
            return jsonify({'error': 'Equipo no encontrado'}), 404
            
        row_index = df[df['Nombre'] == nombre].index[0]
        # Convertir valores entrantes a los tipos correctos
        for key, value in updates.items():
            if key in ['x', 'y', 'Enc_NProd', 'Enc_Prod', 'Alert', 'Rad']:
                df.at[row_index, key] = float(value) if value else 0.0  # Convertir a float, usar 0.0 si está vacío
            elif key == 'Area':
                df.at[row_index, key] = str(value) if value else ''
                
        df.to_excel(excel_file, index=False)
        
        return jsonify({'message': 'Datos actualizados correctamente'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ************************** RUTAS ADD OBJECT ***********************************

@monitoreo_bp.route('/add_object', methods=['POST'])
def add_object():
    try:
        # Obtener datos del formulario
        data = request.form
        nave = data.get('Nave')
        if nave not in ['1', '2']:
            return jsonify({'error': 'Nave inválida'}), 400

        # Definir la ruta del archivo Excel según la nave
        excel_file = os.path.join(UPLOAD_FOLDER, f'coordenadas{nave}.xlsx')
        
        # Leer el archivo Excel existente si existe
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
        
        equipo=str(data.get('Nombre'))
        if equipo in df["Nombre"].values:
            return jsonify({'error': 'Equipo ya existente en base de datos'}), 400
        else:
            # Crear nueva fila con los datos
            new_row = {
                'Nombre': str(data.get('Nombre')),
                'x': float(data.get('x')),
                'y': float(data.get('y')),
                'Enc_NProd': float(data.get('Enc_NProd')),
                'Enc_Prod': float(data.get('Enc_Prod')),
                'Alert': float(data.get('Alert')),
                'Rad': float(data.get('Rad')),
                'Area': str(data.get('Area'))
            }

            # Validar el valor de UAP (Area)
            valid_areas = ['INYECCIÓN', 'PINTURA', 'REVESTIMIENTOS', 'TABLEROS', 
                        'SERV GENERALES', 'ACCESORIOS']
            if new_row['Area'] not in valid_areas:
                return jsonify({'error': 'UAP inválida'}), 400

            # Agregar la nueva fila al dataframe
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Guardar el dataframe actualizado en el archivo Excel
            df.to_excel(excel_file, index=False)

            return jsonify({'message': 'Equipo agregado exitosamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# ++++++++++++++++++++++++ RUTAS DELETE OBJECT ++++++++++++++++++++++++++++++

@monitoreo_bp.route('/delete_object', methods=['POST'])
def delete_object():
    try:
        data = request.json
        nombre = data.get('nombre')
        nave = data.get('nave')
        
        if not nombre or not nave:
            return jsonify({'error': 'Nombre o nave no proporcionados'}), 400
            
        excel_file = os.path.join(UPLOAD_FOLDER, f'coordenadas{nave}.xlsx')
        if not os.path.exists(excel_file):
            return jsonify({'error': f'Archivo {excel_file} no encontrado'}), 404
              
        # Leer Excel
        df = pd.read_excel(excel_file)
        
        if nombre not in df['Nombre'].values:
            return jsonify({'error': f'Equipo {nombre} no encontrado en Nave {nave}'}), 404
            
        # Eliminar la fila donde Nombre coincide
        df = df[df['Nombre'] != nombre]

        # Reindexar y guardar en Excel
        df.reset_index(drop=True, inplace=True)
        try:
            df.to_excel(excel_file, index=False)
        except Exception as e:
            return jsonify({'error': f'Error al guardar el archivo: {str(e)}'}), 500
            
        return jsonify({'message': 'Equipo eliminado correctamente'})
        
    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500
    
# ++++++++++++++++++++++ RUTA LAYOUT ACTUALIZACION +++++++++++++++++++++++++

@monitoreo_bp.route('/upload_map', methods=['POST'])
def upload_map():
    try:
        # Verificar si se subió un archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        file = request.files['file']
        
        # Verificar si el archivo está vacío
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        # Obtener la opción seleccionada (Nave1 o Nave2)
        nave = request.form.get('nave')
        if not nave or nave not in ['Nave1', 'Nave2']:
            return jsonify({'error': 'Seleccione una nave válida'}), 400
        
        # Validar el archivo
        if file and allowed_filemap(file.filename):
            # Definir el nombre del archivo según la nave seleccionada
            filename = f"{nave}.jpg"
            file_path = os.path.join('static/mapas', filename)
            
            # Guardar el archivo (sobrescribe si ya existe)
            file.save(file_path)
            return jsonify({'message': 'Layout actualizado correctamente'})
        else:
            return jsonify({'error': 'Solo se permiten archivos JPG'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500
    
    
# ++++++++++++++++++++++++++++ RUTAS PARA EDITAR LISTA DE CORREOS +++++++++++++++++++++++++++++++

@monitoreo_bp.route('/get_emails', methods=['GET'])
def get_emails():
    try:
        EXCEL_Mails = os.path.join(UPLOAD_FOLDER, 'Correos.xlsx')
        if not os.path.exists(EXCEL_Mails):
            return jsonify({'success': False, 'message': 'El archivo Correos.xlsx no existe.'})
        
        df = pd.read_excel(EXCEL_Mails)
        if 'Correos' not in df.columns:
            return jsonify({'success': False, 'message': 'La columna "Correos" no existe en el archivo.'})
        
        emails = sorted(df['Correos'].dropna().unique().tolist())
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al leer el archivo: {str(e)}'})
    
@monitoreo_bp.route('/delete_email', methods=['POST'])
def delete_email():
    try:
        EXCEL_Mails = os.path.join(UPLOAD_FOLDER, 'Correos.xlsx')
        data = request.get_json()
        email_to_delete = data.get('email')
        
        if not email_to_delete:
            return jsonify({'success': False, 'message': 'No se proporcionó un correo para eliminar.'})
        
        df = pd.read_excel(EXCEL_Mails)
        if 'Correos' not in df.columns:
            return jsonify({'success': False, 'message': 'La columna "Correos" no existe en el archivo.'})
        
        df = df[df['Correos'] != email_to_delete].dropna().reset_index(drop=True)
        df.to_excel(EXCEL_Mails, index=False)
        
        emails = sorted(df['Correos'].unique().tolist())
        return jsonify({'success': True, 'message': 'Correo eliminado con éxito.', 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al eliminar el correo: {str(e)}'})
    

@monitoreo_bp.route('/add_email', methods=['POST'])
def add_email():
    try:
        EXCEL_Mails = os.path.join(UPLOAD_FOLDER, 'Correos.xlsx')
        data = request.get_json()
        new_email = data.get('email')
        
        if not new_email:
            return jsonify({'success': False, 'message': 'No se proporcionó un correo para añadir.'})
        
        # Basic email validation
        if '@' not in new_email or '.' not in new_email:
            return jsonify({'success': False, 'message': 'Correo inválido.'})
        
        df = pd.read_excel(EXCEL_Mails) if os.path.exists(EXCEL_Mails) else pd.DataFrame(columns=['Correos'])
        if new_email in df['Correos'].values:
            return jsonify({'success': False, 'message': 'El correo ya existe en la lista.'})
        
        new_df = pd.DataFrame({'Correos': [new_email]})
        df = pd.concat([df, new_df], ignore_index=True).dropna().reset_index(drop=True)
        df.to_excel(EXCEL_Mails, index=False)
        
        emails = sorted(df['Correos'].unique().tolist())
        return jsonify({'success': True, 'message': 'Correo añadido con éxito.', 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al añadir el correo: {str(e)}'})