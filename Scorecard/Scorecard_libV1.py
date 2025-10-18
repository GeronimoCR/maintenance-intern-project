import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


def modify_data(dfI):
    try:
        def secuencia(lista):
            resultado = []
            i = 0
            while i < len(lista) - 1:
                if lista[i] + 1 == lista[i + 1]:  
                    count = 1
                    while i + count < len(lista) and lista[i + count] == lista[i] + count:
                        count += 1
                    resultado.append([lista[i], count])
                    i += count  
                else:
                    i += 1
            return resultado
    
        IMC = list(dfI[dfI["DS_PLANT"].isnull()].index)
        IMC2 = secuencia(IMC)

        for i in IMC2:
            for j in range(i[1]):
                IMC.remove(i[0]+j)

        Delete = []
        L1 = list(dfI.columns)[3:]
        L2 = list(dfI.columns)[1:17]

        for i in IMC:
            Delete.append(i+1) 

        # Desplazamiento simple
        for i in IMC:
            N0 = dfI["DS_WORK_ORDER"].iloc[i]
            N1 = dfI["DT_WORK_ORDER"].iloc[i+1]
            N2 = str(N0) + "\n" + str(N1)
            dfI.at[dfI.index[i], "DS_WORK_ORDER"] = N2

            for j in range(16):
                dfI.at[dfI.index[i], L1[j]] = dfI[L2[j]].iloc[i+1] 

        for i in IMC2:
            T1 = dfI['DS_WORK_ORDER'].iloc[i[0]]
            for x in range(1, i[1]+1):
                T1 = str(T1) + "\n" + str(dfI['DT_WORK_ORDER'].iloc[i[0] + x]) 
            dfI.at[dfI.index[i[0]], 'DS_WORK_ORDER'] = T1 

        for i in IMC2:
            for j in range(16):
                dfI.at[dfI.index[i[0]], L1[j]] = dfI[L2[j]].iloc[i[0]+i[1]]  
            for k in range(1, i[1]+1):
                Delete.append(i[0]+k)

        # Eliminar filas
        dfI = dfI.drop(dfI.index[Delete])

        # Validación final
        if len(dfI[dfI["DS_WORK_ORDER_TYPE"].isna()]) > 0:
            print("ERROR", "No se pudo limpiar el archivo necesita actualizacion")
        else:
            print("Exito", "Excel limpiado con exito")
        return dfI 

    except Exception as e:
        print("Error", f"No se pudieron modificar los datos .\n{e}")
        return None


def parse_date(date_str):
    try:
        if '-' in date_str:
            # Formato AAAA-dd-MM HH:mm:ss
            date_obj = datetime.strptime(date_str, '%Y-%d-%m %H:%M:%S')
        elif '/' in date_str:
            # Formato MM/dd/AAAA HH:mm:ss
            date_obj = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
        return date_obj
    except ValueError:
        return pd.NaT

def datreq(columna,datfram):
    datcel = datfram.iloc[0][columna]
    return datcel

def nhrs(datfram):
    st=0
    for t in datfram['Minutos']:
        if pd.isna(t):
            t=0
        st+=t
    return st

def TopSem(sem,uap):
    if uap==None:
        Ag=sem
        Area=sem.loc[sem.Tipo=="ZPM1"]
    else:
        Ag=sem.loc[sem.UAP==uap]
        Area=sem.loc[(sem.UAP==uap)&(sem.Tipo=="ZPM1")]
    Averias = pd.DataFrame(columns=["Semana","Orden","UAP","SAP","Equipo","Area","Comentario","Minutos","Registros"])
    Area.reset_index(drop=True, inplace=True)
    for ord in list(Area.Orden.unique()):
        dfT=Area.loc[Area.Orden==ord]
        semana=datreq("Semana",dfT)
        orden=int(ord)
        uaps=datreq("UAP",dfT)
        sap=datreq("SAP",dfT)
        equipo=datreq("Equipo",dfT)
        area=datreq("Area",dfT)
        comentario=datreq("Comentario",dfT)
        minutos=nhrs(dfT)
        registros=dfT.shape[0]
        Averia=[semana,orden,uaps,sap,equipo,area,comentario,minutos,registros]
        Averias.loc[len(Averias)]=Averia
    Averias=Averias.sort_values(by="Minutos",ascending=False)
    Averias.reset_index(drop=True, inplace=True)
    nombres = [
    f"{id_ if pd.notna(id_) else ''}\n" + 
    '\n'.join([' '.join((nombre if pd.notna(nombre) else '').split()[i:i+2]) for i in range(0, len((nombre if pd.notna(nombre) else '').split()), 2)]) + "\n" +
    '\n'.join([' '.join((com if pd.notna(com) else '').split()[i:i+2]) for i in range(0, len((com if pd.notna(com) else '').split()), 2)])
    for id_, nombre, com in zip(Averias.SAP, Averias.Equipo, Averias.Comentario)
    ]
    return Ag,Averias,nombres


def regTemp(P,UAP,dfsegl):
    if P=="Men":
        PT=sorted(list(dfsegl.Mes.unique()))
        regT=pd.DataFrame(columns=["Mes","Minutos totales","No. registros", "MTTR"])
        colf="Mes"
    elif P== "Sem":
        PT=sorted(list(dfsegl.Semana.unique()))
        regT=pd.DataFrame(columns=["Semana","Minutos totales","No. registros", "MTTR"])
        colf="Semana"
    nombres=[]
    for p in PT:
        seglt=dfsegl.loc[(dfsegl[colf]==p)&(dfsegl.UAP==UAP)&(dfsegl.Tipo=="ZPM1")]
        per=int(p)
        minutos=nhrs(seglt)
        regs=int(len(list(seglt.Orden.unique())))
        mttr = minutos / regs if regs != 0 else 0
        regTa=[per,minutos,regs,mttr]
        regT.loc[len(regT)]=regTa
        nombres.append(colf+"\n"+str(p))
    return regT, nombres


def mtbf(sem,uap,Taper):
    uapAV=sem.loc[(sem.UAP==uap)&(sem.Tipo=="ZPM1")]
    MTBFuap=pd.DataFrame(columns=["Area","T apertura (mins)","Num averia","MTBF"])
    for ar in list(uapAV.Area.unique()):
        dfUAT=uapAV.loc[(uapAV.Area==ar)]
        if not(ar in Taper.loc[Taper.UAP==uap,["Area"]].values):
            taper=24*60*5.6
        else:
            taper=Taper.loc[(Taper.UAP==uap)&(Taper.Area==ar),"T apertura (ajustar si es necesario)"].iloc[0]
        numParos=len(list(dfUAT.Orden.unique()))
        mtbf = taper if numParos == 0 else taper / numParos
        mtbfar=[ar,taper,numParos,mtbf]
        MTBFuap.loc[len(MTBFuap)]=mtbfar
    AreasT = Taper.loc[Taper.UAP == uap, ["Area", "T apertura (ajustar si es necesario)"]]
    MTBFuap = AreasT.merge(MTBFuap, on='Area', how='outer')
    MTBFuap['Num averia'] = pd.to_numeric(MTBFuap['Num averia'], errors='coerce').fillna(0).astype(int)
    MTBFuap['T apertura (mins)'] = pd.to_numeric(MTBFuap['T apertura (mins)'], errors='coerce').fillna(pd.to_numeric(MTBFuap['T apertura (ajustar si es necesario)'], errors='coerce'))
    MTBFuap['MTBF'] = pd.to_numeric(MTBFuap['MTBF'], errors='coerce').fillna(pd.to_numeric(MTBFuap['T apertura (ajustar si es necesario)'], errors='coerce'))
    MTBFuap = MTBFuap.drop(columns=['T apertura (ajustar si es necesario)'])
    MTBFuap=MTBFuap.sort_values(by="MTBF",ascending=False)
    return MTBFuap


def mttr(sem,uap,Taper):
    uapAV=sem.loc[(sem.UAP==uap)&(sem.Tipo=="ZPM1")]
    MTTRuap=pd.DataFrame(columns=["Area","Mins averia","Num averia","MTTR"])
    for ar in list(uapAV.Area.unique()):
        dfUAT=uapAV.loc[(uapAV.Area==ar)]
        mins=nhrs(dfUAT)
        numParos=len(list(dfUAT.Orden.unique()))
        mttr = 0 if numParos == 0 else mins / numParos
        mttrar=[ar,mins,numParos,mttr]
        MTTRuap.loc[len(MTTRuap)]=mttrar
    AreasT= Taper.loc[Taper.UAP==uap,["Area"]]
    MTTRuap = AreasT.merge(MTTRuap, on='Area', how='outer')
    MTTRuap['Mins averia'] = pd.to_numeric(MTTRuap['Mins averia'], errors='coerce').fillna(0)
    MTTRuap['Num averia'] = pd.to_numeric(MTTRuap['Num averia'], errors='coerce').fillna(0).astype(int)
    MTTRuap['MTTR'] = pd.to_numeric(MTTRuap['MTTR'], errors='coerce').fillna(0)
    MTTRuap=MTTRuap.sort_values(by="MTTR",ascending=False)
    return MTTRuap


def mtbfM(Men,uap,Taper):
    uapAV=Men.loc[(Men.UAP==uap)&(Men.Tipo=="ZPM1")]
    MTBFuap=pd.DataFrame(columns=["Area","Min apertura (Men)","Num averia","MTBF"])
    for ar in list(uapAV.Area.unique()):
        dfUAT=uapAV.loc[(uapAV.Area==ar)]
        if not(ar in Taper.loc[Taper.UAP==uap,["Area"]].values):
            taper=(24*60*5.6)*4
        else:
            taper=(Taper.loc[(Taper.UAP==uap)&(Taper.Area==ar),"T apertura (ajustar si es necesario)"].iloc[0])*4
        numParos=len(list(dfUAT.Orden.unique()))
        mtbf = taper if numParos == 0 else taper / numParos
        mtbfar=[ar,taper,numParos,mtbf]
        MTBFuap.loc[len(MTBFuap)]=mtbfar
    AreasT = Taper.loc[Taper.UAP == uap, ["Area", "T apertura (ajustar si es necesario)"]]
    MTBFuap = AreasT.merge(MTBFuap, on='Area', how='outer')
    MTBFuap['Num averia'] = MTBFuap['Num averia'].fillna(0)
    MTBFuap['Min apertura (Men)'] = MTBFuap['Min apertura (Men)'].fillna((MTBFuap['T apertura (ajustar si es necesario)'])*4)
    MTBFuap['MTBF'] = MTBFuap['MTBF'].fillna((MTBFuap['T apertura (ajustar si es necesario)'])*4)
    MTBFuap = MTBFuap.drop(columns=['T apertura (ajustar si es necesario)'])
    MTBFuap=MTBFuap.sort_values(by="MTBF",ascending=False)
    return MTBFuap


def mttrM(Men,uap,Taper):
    uapAV=Men.loc[(Men.UAP==uap)&(Men.Tipo=="ZPM1")]
    MTTRuap=pd.DataFrame(columns=["Area","Mins averia (Men)","Num averia","MTTR"])
    for ar in list(uapAV.Area.unique()):
        dfUAT=uapAV.loc[(uapAV.Area==ar)]
        mins=nhrs(dfUAT)
        numParos=len(list(dfUAT.Orden.unique()))
        mttr = 0 if numParos == 0 else mins / numParos
        mttrar=[ar,mins,numParos,mttr]
        MTTRuap.loc[len(MTTRuap)]=mttrar
    AreasT= Taper.loc[Taper.UAP==uap,["Area"]]
    MTTRuap = AreasT.merge(MTTRuap, on='Area', how='outer')
    MTTRuap[['Mins averia (Men)', 'Num averia', 'MTTR']] = MTTRuap[['Mins averia (Men)', 'Num averia', 'MTTR']].fillna(0)
    MTTRuap=MTTRuap.sort_values(by="MTTR",ascending=False)
    return MTTRuap


def efTecUAP(sem,UAP,TecsT,infT):
    dfTecEf=pd.DataFrame(columns=["Semana","UAP","Tecnico","Turno","T extra","Min semanales","Min Preventivos","Min Averias","Min Correctivos","%T util"])
    for tec in list(sem.loc[(sem.UAP==UAP)].Tecnico.unique()):
        semn=sem.Semana.iloc[0]
        uap=UAP
        turno=TecsT.loc[(TecsT.UAP==UAP)&(TecsT.Tecnico==tec),"Turno"].iloc[0]
        textra=TecsT.loc[(TecsT.UAP==UAP)&(TecsT.Tecnico==tec),"T extra (hrs)"].iloc[0]
        Tprev=nhrs(sem.loc[(sem.Tipo=="ZPM2")&(sem.UAP==UAP)&(sem.Tecnico==tec)])
        Tave=nhrs(sem.loc[(sem.Tipo=="ZPM1")&(sem.UAP==UAP)&(sem.Tecnico==tec)])
        Tcorr=nhrs(sem.loc[(sem.Tipo=="ZPM4")&(sem.UAP==UAP)&(sem.Tecnico==tec)])
        Minturno=infT.loc[infT.Turno==turno,"Sem"].iloc[0]
        MinExt=textra*60
        MinSem=Minturno+MinExt
        PerPrev = Tprev / MinSem if MinSem != 0 else 0
        PerAve = Tave / MinSem if MinSem != 0 else 0
        PerCorr = Tcorr / MinSem if MinSem != 0 else 0
        PerTutil=PerPrev+PerAve+PerCorr
        tecef=[semn,uap,tec,turno,textra,MinSem,Tprev,Tave,Tcorr,PerTutil]
        dfTecEf.loc[len(dfTecEf)]=tecef
    dfTecEf=dfTecEf.sort_values(by="%T util",ascending=False)
    dfTecEf = dfTecEf.reset_index(drop=True)
    return dfTecEf
        
def efTecTOTAL(sem,TecsT,infT):
    dfTecEfT=pd.DataFrame(columns=["Semana","UAP","Tecnico","Turno","T extra","Min semanales","Min Preventivos","Min Averias","Min Correctivos","%T util"])
    for uap in list(sem.UAP.unique()):
        eftcsuap=efTecUAP(sem,uap,TecsT,infT)
        dfTecEfT = pd.concat([dfTecEfT, eftcsuap], ignore_index=True)
    dfTecEfT = dfTecEfT.sort_values(by="%T util", ascending=False)
    dfTecEfT = dfTecEfT.reset_index(drop=True)
    return dfTecEfT
    
def prev_inf(ac,seglab,uap,sem=None):
    if ac:
        dfPrev=pd.DataFrame(columns=["Semana","UAP","Total prev","Total tareas","Minutos"])
        nombres=[]
        for semn in sorted(list(seglab.Semana.unique())):
            dfpt=seglab.loc[(seglab.Semana==semn)&(seglab.UAP==uap)&(seglab.Tipo=="ZPM2")]
            semana=semn
            ua=uap
            TPrevs=len(list(dfpt.Orden.unique()))
            TTasks=len(dfpt.Orden.to_list())
            mins=nhrs(dfpt)
            s=[semana,ua,TPrevs,TTasks,mins]
            dfPrev.loc[len(dfPrev)]=s
            nombres.append("Sem\n"+str(semn))
        return dfPrev, nombres
    else:
        dfPrev=pd.DataFrame(columns=["Semana","UAP","Orden","SAP","Equipo","Total tareas","Tecnico","Minutos"])
        dfSP=seglab.loc[(seglab.Semana==sem)&(seglab.Tipo=="ZPM2")&(seglab.UAP==uap)]
        for ord in list(dfSP.Orden.unique()):
            semana=sem
            ua=uap
            orn=ord
            sap=dfSP.loc[dfSP.Orden==ord,"SAP"].iloc[0]
            equ=dfSP.loc[dfSP.Orden==ord,"Equipo"].iloc[0]
            ttask=len(dfSP.loc[dfSP.Orden==ord].Orden.to_list())
            tec=dfSP.loc[dfSP.Orden==ord,"Tecnico"].iloc[0]
            mins=nhrs(dfSP.loc[dfSP.Orden==ord])
            ors=[semana,ua,orn,sap,equ,ttask,tec,mins]
            dfPrev.loc[len(dfPrev)]=ors
        dfPrev.sort_values(by="Minutos", ascending=False, inplace=True)
        nombres = [
                f"{orden}\n"
                f"{sap}\n" +
                '\n'.join([' '.join(equipo.split()[i:i+2]) 
                        for i in range(0, len(equipo.split()), 2)])
                for orden, sap, equipo in zip(dfPrev.Orden, dfPrev.SAP, dfPrev.Equipo)
                ]
        return dfPrev.reset_index(drop=True),nombres



def graficar(nombres, Mins, registros, op, area, semana, TLetra):
    # Configuración dinámica
    num_equipos = len(nombres)
    ancho_figura = max(8, num_equipos * 0.8)  # Aumentar factor a 1.0 para más espacio
    TLetra = min(TLetra, max(6, 12 - num_equipos * 0.3))  # Tamaño de fuente dinámico

    # Etiquetas para las barras
    etiquetas = (
        [f"{n}\nMin: {m:.1f}" for n, m in zip(nombres, Mins)] if op == "Top" else
        [f"{n}\nMin: {m:.1f}\nReg: {r}" for n, m, r in zip(nombres, Mins, registros)]
    )
    fig, ax1 = plt.subplots(figsize=(ancho_figura, 6))
    x = np.linspace(0, num_equipos - 1, num_equipos) * 1.2  # Espaciado ajustado
    ancho_barra = 0.7 * (10 / num_equipos) if num_equipos > 10 else 0.7  # Ancho dinámico
    barras = ax1.bar(x, Mins, color='#00a8e8', label='Minutos de avería', width=ancho_barra)
    ax1.set_ylabel("Minutos de avería", color='#00a8e8')
    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, rotation=0, ha="center", fontsize=TLetra, fontweight="bold")
    # Ajustar límites del eje X para usar todo el espacio
    ax1.set_xlim(-0.5, (num_equipos - 1) * 1.2 + 0.5)
    if op == "Top":
        ax1.grid(True, axis='y', linestyle='--', alpha=0.7) 
        ax1.legend(handles=[barras], loc='upper right')
    else:
        ax2 = ax1.twinx()
        linea, = ax2.plot(x, registros, color='#d62828', marker='o', linestyle='-', linewidth=2, label='Registros de avería')
        ax2.set_ylabel("Registros de avería", color='#d62828')
        ax1.legend(handles=[barras, linea], loc='upper right')
    plt.title(
        f"Máquinas con más minutos de avería {area} SEM {semana}" if op == "Top" else
        f"Número y minutos de avería en {area} {'semanal' if op == 'Sem' else 'mensual'}"
    )
    plt.tight_layout()
    #plt.show()
    return fig

def graficar_indicador(df, uap, col_cats, col_ind, p, ejX, fz, unidad=None, objetivo=None, tipo_objetivo=None, periodo="semana"):
    # Extraer datos
    categorias = df[col_cats].tolist()
    valores = df[col_ind].tolist()
    num_cats = len(categorias)
    # Configuración de la figura
    fig, ax = plt.subplots(figsize=(max(8, num_cats * 1), 6))
    x = np.arange(num_cats)
    # Barras
    ax.bar(x, valores, color='#00a8e8', label=col_ind, width=0.4)
    # Etiquetas
    etiquetas = [f"{cat}\n{val:.2f}" for cat, val in zip(categorias, valores)]
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas, fontsize=fz, fontweight='bold', ha='center')
    # Ejes y título
    ax.set_ylabel(f"{col_ind} ({unidad})" if unidad else col_ind, color='#00a8e8')
    ax.set_xlabel(ejX)
    ax.set_title(f"{col_ind} en {uap} {periodo} {p}")
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    ax.legend()
    if objetivo is not None:
        # Determinar el texto de la leyenda según tipo_objetivo
        texto_objetivo = f"Objetivo {'máximo' if tipo_objetivo == 'maximo' else 'mínimo' if tipo_objetivo == 'minimo' else ''}: {objetivo}"
        ax.axhline(y=objetivo, color='#d62828', linestyle='--', linewidth=1.7, label=texto_objetivo)
        ax.text(-0.6, objetivo+0.02*(ax.get_ylim()[1]-ax.get_ylim()[0]), f'{objetivo}', color='#d62828', va='center', ha='right', fontsize=8)
        ax.legend()
    plt.tight_layout()
    return fig

def graf_prev(total_prev, total_tareas, minutos, nombres, opcion, semana, uap):
    n = len(nombres)
    ancho_figura = max(10, n * 1.0)
    TLetra = min(8, max(6, 12 - n * 0.3)) if opcion == 'AC' else min(8, max(5, 10 - n * 0.5))
    if opcion == 'AC':
        etiquetas = [f"{n}\nPrev: {p}\nTareas: {t}\nMin: {m:.1f}" 
                     for n, p, t, m in zip(nombres, total_prev, total_tareas, minutos)]
    else:
        etiquetas = [f"{n}\nTareas: {t}\nMin: {m:.1f}" 
                     for n, t, m in zip(nombres, total_tareas, minutos)]
    fig, ax1 = plt.subplots(figsize=(ancho_figura, 6))
    x = np.linspace(0, n - 1, n) * 1.5
    ancho_barra = 0.7 * (10 / n) if n > 10 else 0.7
    if opcion == 'AC':
        ax1.bar(x - ancho_barra/4, total_prev, ancho_barra/2, label='Total Prev', color='#f77f00')
        ax1.bar(x + ancho_barra/4, total_tareas, ancho_barra/2, label='Total tareas', color='#003049')
        ax2 = ax1.twinx()
        ax2.plot(x, minutos, color='#d62828', linestyle='-', marker='o', label='Minutos', linewidth=2, markersize=8) 
        ax1.set_ylabel('No. prev / No. tareas', fontsize=12)
        ax2.set_ylabel('Minutos', fontsize=12, color='#d62828')
        ax2.tick_params(axis='y', labelcolor='#d62828')
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)
    elif opcion == 'SEM':
        ax1.bar(x, minutos, ancho_barra, label='Minutos', color='#003049')
        ax2 = ax1.twinx()
        ax2.plot(x, total_tareas, color='#d62828', linestyle='-', marker='o', label='Total tareas', linewidth=2, markersize=8) 
        ax1.set_ylabel('Minutos', fontsize=12)
        ax2.set_ylabel('Total tareas', fontsize=12, color='#d62828')
        ax2.tick_params(axis='y', labelcolor='#d62828')        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, rotation=0, ha='center', fontsize=TLetra, fontweight='bold')
    ax1.set_xlim(-0.5, (n - 1) * 1.5 + 0.5)
    if opcion == 'AC':
        plt.title(f'Preventivos realizados semanalmente {uap}', fontsize=14)
    else: 
        plt.title(f'Preventivos realizados en {uap} semana {semana}', fontsize=14)
    ax1.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    #plt.show()
    return fig



def Doc_Cleaned(dfi, dfAEAct, infTurnos, dfTApertura):
    dfi['DT_WORK_ORDER'] = dfi['DT_WORK_ORDER'].astype(str)
    dfi['Fecha'] = dfi['DT_WORK_ORDER'].apply(parse_date)
    dfi['Fecha'] = dfi['Fecha'].dt.strftime('%d/%m/%Y %H:%M:%S')
    dfi['Fecha'] = pd.to_datetime(dfi['Fecha'], format='%d/%m/%Y %H:%M:%S')
    seglab = pd.DataFrame()
    seglab["Fecha"]=dfi["Fecha"]
    seglab['Dia'] = dfi['Fecha'].dt.day
    seglab['Mes'] = dfi['Fecha'].dt.month
    seglab['Año'] = dfi['Fecha'].dt.year
    seglab['Semana'] = dfi['Fecha'].dt.isocalendar().week
    seglab["Orden"]=dfi["ID_WORK_ORDER"]
    seglab["SAP"]=dfi["ID_EQUIP"]
    seglab["Equipo"]=dfi["DS_EQUIP"]
    seglab["Tipo"]=dfi["ID_WORK_ORDER_TYPE"]
    seglab["UAP"]=dfi["ID_WORKC_PM"]
    seglab['Area'] = seglab['SAP'].map(dfAEAct.set_index('SAP')['Area'].to_dict()).fillna('NE')
    seglab["Tecnico"]=dfi["DS_EMPLO"]
    seglab["Comentario"]=dfi["DS_WORK_ORDER"]
    seglab["Horas"]=dfi["QT_HOURS_SUM"]
    seglab["Minutos"]=dfi["QT_MINUT_SUM"]
    seglab=seglab.sort_values(by="Fecha")

    dfTecs = pd.DataFrame(columns=["UAP", "Tecnico", "Turno","T extra (hrs)"])
    for ua in list(seglab.UAP.unique()):
        tecnicos = list(seglab.loc[seglab.UAP == ua].Tecnico.unique())
        if not tecnicos:
            continue
        dfTecsT = pd.DataFrame({
            "Tecnico": tecnicos,
            "UAP": ua,
            "Turno": "",
            "T extra (hrs)":0
        })
        dfTecs = pd.concat([dfTecs, dfTecsT], ignore_index=True)
    
    return seglab,dfTecs,infTurnos,dfTApertura,dfAEAct


def UAP_SCR(Seglab,SeglabSP,IDuap,Nuap,Tec_Turn, InfTurn,dfTAp,Semana):
    uapGSP,AveriasuapSP, NombresuapSP =TopSem(SeglabSP,IDuap)
    uapMen, NombMenuap =regTemp("Men",IDuap,Seglab)
    uapSem, NombSemuap =regTemp("Sem",IDuap,Seglab)
    MTBFuapSP=mtbf(SeglabSP,IDuap,dfTAp)
    MTTRuapSP=mttr(SeglabSP,IDuap,dfTAp)
    EfTecuapSP=efTecUAP(SeglabSP,IDuap,Tec_Turn,InfTurn)
    PrevuapAC,NomPrevuapAC=prev_inf(True,Seglab,IDuap)
    PrevuapSEM,NomPrevuapSEM=prev_inf(False,Seglab,IDuap,Semana)

    Dfsuap=[
        uapGSP,
        AveriasuapSP,
        uapMen,
        uapSem,
        MTBFuapSP,
        MTTRuapSP,
        EfTecuapSP,
        PrevuapAC,
        PrevuapSEM
    ]
    Figsuap=[
    graficar(NombresuapSP[:10], AveriasuapSP.Minutos.head(10), AveriasuapSP.Registros.head(10),"Top", Nuap, Semana, 5),
    graficar(NombMenuap, uapMen["Minutos totales"], uapMen["No. registros"],"Men", Nuap, Semana, 8),
    graficar(NombSemuap[-10:], uapSem["Minutos totales"].tail(10), uapSem["No. registros"].tail(10),"Sem", Nuap, Semana, 8),
    graficar_indicador(MTBFuapSP, Nuap, "Area", "MTBF", Semana, "Areas", 8, "Minutos", 488, "minimo", "semana"),
    graficar_indicador(MTTRuapSP, Nuap, "Area", "MTTR", Semana, "Areas", 8, "Minutos", 60, "maximo", "semana"),
    graficar_indicador(EfTecuapSP, Nuap, "Tecnico", "%T util", Semana, "Tecnicos", 5,None, 0.75, "minimo", "semana"),
    graf_prev(PrevuapAC["Total prev"].tail(10), PrevuapAC["Total tareas"].tail(10), PrevuapAC["Minutos"].tail(10), NomPrevuapAC[-10:], "AC", Semana, Nuap),
    graf_prev(None, PrevuapSEM["Total tareas"].head(10), PrevuapSEM["Minutos"].head(10), NomPrevuapSEM[:10], "SEM", Semana, Nuap)
    ]


    return Dfsuap, Figsuap


def tecs_SCR(SeglabSP,Tec_Turn,InfTurn,Semana):
    dfTecsT=[efTecTOTAL(SeglabSP,Tec_Turn,InfTurn)]
    Figs_TecsT=[graficar_indicador(dfTecsT[0].head(10), "General", "Tecnico", "%T util", Semana, "Tecnicos", 5, None, 0.75, "minimo", "semana")]
    return dfTecsT, Figs_TecsT