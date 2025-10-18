import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


def ConsGral(dfMed,EqUAP):
    dfMed['Date'] = pd.to_datetime(dfMed['Date'], format='%d/%m/%Y %H:%M:%S')
    ConsMen = dfMed.groupby('Title')['Value'].sum().reset_index()
    ConsMen.columns = ['Maquina', 'Consumo (KWh)']
    dict_uap = EqUAP.set_index('MAQUINA')['UAP'].to_dict()
    ConsMen['UAP'] = ConsMen['Maquina'].map(dict_uap)
    ConsMen['Inicio periodo']=dfMed['Date'].min()
    ConsMen['Fin periodo']=dfMed['Date'].max()
    ConsMen = ConsMen.dropna(subset=['UAP'])
    ConsMen = ConsMen.sort_values(by='Consumo (KWh)', ascending=False).reset_index(drop=True)
    return ConsMen


def top10Plt(df, uap_name):
    top10 = df.head(10)
    # Crear etiquetas para el eje X
    labels = [
        '\n'.join([' '.join(maquina.split()[i:i+1]) for i in range(0, len(maquina.split()), 1)])
        for maquina in top10['Maquina']
    ]
    
    inicio = top10['Inicio periodo'].iloc[0].strftime('%d/%m/%Y %H:%M:%S')
    fin = top10['Fin periodo'].iloc[0].strftime('%d/%m/%Y %H:%M:%S')
    
    # Crear la figura y la gráfica de barras
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
    ax.set_facecolor('white')
    
    # Definir paleta de colores para el gradiente dentro de cada barra
    colors = ['#4C78A8', '#6BAED6']  # Azul suave a azul más claro
    cmap = LinearSegmentedColormap.from_list("custom_blue", colors)
    
    # Crear barras con gradiente diagonal
    for i, (label, height) in enumerate(zip(labels, top10['Consumo (KWh)'])):
        # Definir el rectángulo de la barra
        bar = Rectangle((i - 0.4, 0), 0.8, height, edgecolor="#000000", linewidth=1)
        ax.add_patch(bar)
        
        gradient = np.linspace(0, 1, 100)
        gradient = np.vstack((gradient, gradient))
        ax.imshow( 
            gradient,
            cmap=cmap,
            aspect='auto',
            extent=[i - 0.395, i + 0.395, 0, height-height*0.005],
            zorder=bar.get_zorder() + 1,
            alpha=1,
            interpolation='bilinear',
            transform=ax.transData,
            clip_path=bar
        )
        
        # Añadir el valor de consumo encima de la barra
        ax.text(
            i, height + (top10['Consumo (KWh)'].max() * 0.02),  
            f"{height:.2f}",
            ha='center', va='bottom',
            fontsize=10, color="#000000", fontfamily='Arial'
        )
    
    # Configurar límites del eje
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(0, top10['Consumo (KWh)'].max() * 1.1) 
    
    # Configurar título
    ax.set_title(
        f"Consumo energetico en {uap_name} \n Periodo: {inicio} - {fin} ",
        fontsize=18,
        fontweight='bold',
        color="#000000",
        pad=15,
        fontfamily='Arial'
    )
    
    # Configurar etiquetas de los ejes
    ax.set_xlabel('Máquina', fontsize=14, color="#000000", fontfamily='Arial')  # Cambiado a 'Máquina'
    ax.set_ylabel('Consumo (KWh)', fontsize=14, color="#000000", fontfamily='Arial')
    
    # Configurar etiquetas del eje X sin rotación y tamaño de fuente reducido
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10, color="#000000", fontfamily='Arial')
    
    # Añadir cuadrícula sutil en el eje Y
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color="#616161")
    ax.set_axisbelow(True)  # Poner la cuadrícula detrás de las barras
    
    # Configurar estilo de los ejes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color("#000000")
    ax.spines['bottom'].set_color("#000000")
    
    # Ajustar diseño para evitar que las etiquetas se corten
    plt.tight_layout()
    
    # Retornar la figura
    return fig



def DataGral(dfMed,EqUAP):
    DfGral= ConsGral(dfMed,EqUAP)
    figGral=top10Plt(DfGral, 'Planta total')
    return DfGral, figGral

def DataUAP(dfMed,EqUAP, UAP):
    DfGral= ConsGral(dfMed,EqUAP)
    DfUAP = DfGral[DfGral['UAP'] == UAP].reset_index(drop=True)
    figUAP=top10Plt(DfUAP, UAP)
    return DfUAP, figUAP



def NavesConMin(dfMedS, MedNav, EqNAVS):
    dfMedS['Date'] = pd.to_datetime(dfMedS['Date'], format='%d/%m/%Y %H:%M:%S')
    dfWKEnd = dfMedS[dfMedS['Date'].dt.weekday.isin([5, 6])]
    medsNaves={}
    countNave=0
    for m in list(MedNav.Medidor.unique()):
        df_med = dfWKEnd[dfWKEnd['Title'] == m].sort_values('Date')
        minMed=df_med['Value'].min()
        dateminMed= df_med.loc[df_med['Value'] == minMed, 'Date'].iloc[0]
        # Obtener fecha anterior más cercana (menor a dateminMed)
        fechasPrev = df_med[df_med['Date'] < dateminMed]
        fechaPrev = fechasPrev['Date'].max() if not fechasPrev.empty else None
        # Obtener fecha posterior más cercana (mayor a dateminMed)
        fechasPost = df_med[df_med['Date'] > dateminMed]
        fechaPost = fechasPost['Date'].min() if not fechasPost.empty else None

        # Crear rango de fechas de minima medicion
        if fechaPrev==None:
            fechasPost2=df_med[df_med['Date'] > fechaPost]
            fechaPost2 =fechasPost2['Date'].min()
            rangeDates=[dateminMed,fechaPost,fechaPost2]

        elif fechaPost==None:
            fechasPrev2=df_med[df_med['Date'] < fechaPrev]
            fechaPrev2 =fechasPrev2['Date'].max()
            rangeDates=[fechaPrev2,fechaPrev,dateminMed]
        else:
            rangeDates=[fechaPrev,dateminMed,fechaPost]

        # Obtener nave del medidor y df solo en el rango de fechas de minima medicion
        nave=MedNav.loc[MedNav['Medidor']==m, 'Nave'].iloc[0]
        dfrange = dfWKEnd.loc[dfWKEnd['Date'].isin(rangeDates)]
        # Crear df agrupando por promedio solo en maquinas del mismo medidor
        ConsWknd =dfrange.groupby('Title')['Value'].mean().reset_index()
        ConsWknd.columns = ['Maquina', 'Consumo promedio (KWh)']
        dict_nave = EqNAVS.set_index('MAQUINA')['NAVE'].to_dict()
        ConsWknd['Nave'] = ConsWknd['Maquina'].map(dict_nave)
        ConsWknd['Inicio periodo']=dfrange['Date'].min()
        ConsWknd['Fin periodo']=dfrange['Date'].max()
        ConsWknd = ConsWknd.loc[ConsWknd['Nave']==nave]
        ConsWknd = ConsWknd.sort_values(by='Consumo promedio (KWh)', ascending=False).reset_index(drop=True)
        IPer = dfrange['Date'].min().strftime('%d/%m/%Y %H:%M:%S')
        FPer = dfrange['Date'].max().strftime('%d/%m/%Y %H:%M:%S')
        medsNaves[f'NAVE {countNave+1}']=[ConsWknd , IPer, FPer]
        countNave += 1
    return medsNaves


def top10Plt_Wknd(df, nave):
    top10 = df.head(10)
    # Crear etiquetas para el eje X
    labels = [
        '\n'.join([' '.join(maquina.split()[i:i+1]) for i in range(0, len(maquina.split()), 1)])
        for maquina in top10['Maquina']
    ]
    
    inicio = top10['Inicio periodo'].iloc[0].strftime('%d/%m/%Y %H:%M:%S')
    fin = top10['Fin periodo'].iloc[0].strftime('%d/%m/%Y %H:%M:%S')
    
    # Crear la figura y la gráfica de barras
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
    ax.set_facecolor('white')
    
    # Definir paleta de colores para el gradiente dentro de cada barra
    colors = ['#4C78A8', '#6BAED6']  # Azul suave a azul más claro
    cmap = LinearSegmentedColormap.from_list("custom_blue", colors)
    
    # Crear barras con gradiente diagonal
    for i, (label, height) in enumerate(zip(labels, top10['Consumo promedio (KWh)'])):
        # Definir el rectángulo de la barra
        bar = Rectangle((i - 0.4, 0), 0.8, height, edgecolor="#000000", linewidth=1)
        ax.add_patch(bar)
        
        gradient = np.linspace(0, 1, 100)
        gradient = np.vstack((gradient, gradient))
        ax.imshow(
            gradient,
            cmap=cmap,
            aspect='auto',
            extent=[i - 0.395, i + 0.395, 0, height-height*0.005],
            zorder=bar.get_zorder() + 1,
            alpha=1,
            interpolation='bilinear',
            transform=ax.transData,
            clip_path=bar
        )
        
        # Añadir el valor de consumo encima de la barra
        ax.text(
            i, height + (top10['Consumo promedio (KWh)'].max() * 0.02),  
            f"{height:.2f}",
            ha='center', va='bottom',
            fontsize=10, color="#000000", fontfamily='Arial'
        )
    
    # Configurar límites del eje
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(0, top10['Consumo promedio (KWh)'].max() * 1.1) 
    
    # Configurar título
    ax.set_title(
        f"Consumo energetico en {nave} \nBase Load:\n{inicio} - {fin} ",
        fontsize=18,
        fontweight='bold',
        color="#000000",
        pad=15,
        fontfamily='Arial'
    )
    
    # Configurar etiquetas de los ejes
    ax.set_xlabel('Máquina', fontsize=14, color="#000000", fontfamily='Arial')  # Cambiado a 'Máquina'
    ax.set_ylabel('Consumo promedio (KWh)', fontsize=14, color="#000000", fontfamily='Arial')
    
    # Configurar etiquetas del eje X sin rotación y tamaño de fuente reducido
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10, color="#000000", fontfamily='Arial')
    
    # Añadir cuadrícula sutil en el eje Y
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color="#616161")
    ax.set_axisbelow(True)  # Poner la cuadrícula detrás de las barras
    
    # Configurar estilo de los ejes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color("#000000")
    ax.spines['bottom'].set_color("#000000")
    
    # Ajustar diseño para evitar que las etiquetas se corten
    plt.tight_layout()
    
    # Retornar la figura
    return fig


def DataNave_Wknd(dfMedS, MedNav, EqNAVS, NAVE):
    dictNaves=NavesConMin(dfMedS, MedNav, EqNAVS)
    DfNave=dictNaves[NAVE][0]
    InPer=dictNaves[NAVE][1]
    FinPer=dictNaves[NAVE][2]

    FigNave=top10Plt_Wknd(DfNave, NAVE)
    return DfNave, FigNave, InPer, FinPer