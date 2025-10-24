from flask import Blueprint, request, jsonify, render_template, send_file, session
from flask_cors import CORS
import pandas as pd
import os
import tempfile
import pickle
from io import BytesIO
from .Scorecard_libV1 import modify_data, Doc_Cleaned, UAP_SCR
import datetime
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

scorecard_bp = Blueprint('scorecard', __name__, template_folder='templates', static_folder='static')
CORS(scorecard_bp)

# Directorio de uploads

# CARPETA DE ARCHIVOS ORIGINALES (del código, NO se modifican)
upload_dir = '/app/uploads/Scorecard'

# CARPETA PERSISTENTE (volumen, se reinicia al deploy/restart)
PERSISTENT_UPLOADS = '/data/Monitoreo'

# Asegurar que existan ambas
os.makedirs(PERSISTENT_UPLOADS, exist_ok=True)

os.makedirs(upload_dir, exist_ok=True)
UAP_OPTIONS = {
    "PM1318IN": "INYECCIÓN",
    "PM1318AC": "ACCESORIOS",
    "PM1318PI": "PINTURA",
    "PM1318RE": "REVESTIMIENTOS",
    "PM1318TA": "TABLEROS",
    "PM1318SG": "SER GEN",
    "PM1318MO": "MOLDES"
}

# Caché global para DataFrames y semanas únicas
DATA_CACHE = {
    'seglab': None,
    'tec_tur': None,
    'inf_turnos': None,
    'df_tprod': None,
    'weeks': None,
    'last_modified': {}  # Tiempos de última modificación de los archivos
}

# Caché para resultados de UAP_SCR
UAP_SCR_CACHE = {}  # Clave: f"{uap}_{week}", Valor: (df_list, fig_list, fig0_path, temp_dir)

def load_dataframes():
    """Carga los DataFrames y semanas únicas en la caché si los archivos han cambiado."""
    files = {
        'seglab': os.path.join(upload_dir, 'Seg lab.xlsx'),
        'tec_tur': os.path.join(upload_dir, 'Tecnicos-Turnos.xlsx'),
        'inf_turnos': os.path.join(upload_dir, 'Inf Turnos.xlsx'),
        'df_tprod': os.path.join(upload_dir, 'T apertura.xlsx')
    }
    
    # Verificar si algún archivo ha cambiado
    files_changed = False
    for key, path in files.items():
        if not os.path.exists(path):
            DATA_CACHE[key] = None
            continue
        current_mtime = os.path.getmtime(path)
        last_mtime = DATA_CACHE['last_modified'].get(key, 0)
        if current_mtime > last_mtime:
            files_changed = True
            DATA_CACHE['last_modified'][key] = current_mtime
    
    if files_changed or any(v is None for v in DATA_CACHE.values() if key != 'weeks'):
        try:
            DATA_CACHE['seglab'] = pd.read_excel(files['seglab']) if os.path.exists(files['seglab']) else None
            DATA_CACHE['tec_tur'] = pd.read_excel(files['tec_tur']) if os.path.exists(files['tec_tur']) else None
            DATA_CACHE['inf_turnos'] = pd.read_excel(files['inf_turnos']) if os.path.exists(files['inf_turnos']) else None
            DATA_CACHE['df_tprod'] = pd.read_excel(files['df_tprod']) if os.path.exists(files['df_tprod']) else None
            DATA_CACHE['weeks'] = sorted(DATA_CACHE['seglab']['Semana'].unique().tolist()) if DATA_CACHE['seglab'] is not None else []
            if files_changed:
                # Limpiar caché y directorios temporales
                for cache_key, (_, _, fig0_path, temp_dir) in list(UAP_SCR_CACHE.items()):
                    try:
                        if os.path.exists(fig0_path):
                            os.remove(fig0_path)
                        if os.path.exists(os.path.join(temp_dir, 'df_list.pkl')):
                            os.remove(os.path.join(temp_dir, 'df_list.pkl'))
                        if os.path.exists(os.path.join(temp_dir, 'fig_list.pkl')):
                            os.remove(os.path.join(temp_dir, 'fig_list.pkl'))
                        if os.path.exists(temp_dir):
                            os.rmdir(temp_dir)
                    except Exception as e:
                        print(f"Error al limpiar directorio temporal {temp_dir}: {e}")
                UAP_SCR_CACHE.clear()
        except Exception as e:
            print(f"Error al cargar DataFrames en caché: {e}")
            DATA_CACHE['seglab'] = None
            DATA_CACHE['tec_tur'] = None
            DATA_CACHE['inf_turnos'] = None
            DATA_CACHE['df_tprod'] = None
            DATA_CACHE['weeks'] = []


@scorecard_bp.route('/ScoreDB')
def database():
    return render_template('Scorecard/ScoreDB.html')

@scorecard_bp.route('/ScoreInfo')
def indicadores():
    # Cargar DataFrames y semanas en caché
    load_dataframes()
    weeks = DATA_CACHE['weeks'] if DATA_CACHE['weeks'] is not None else []
    
    return render_template('Scorecard/ScoreInfo.html', uaps=UAP_OPTIONS.keys(), weeks=weeks)

@scorecard_bp.route('/ScoreIn')
def Scorecard_principal():
    return render_template('Scorecard/ScoreIn.html')

# Ruta para limpiar el archivo y devolver semanas únicas
@scorecard_bp.route('/limpiar_archivo', methods=['POST'])
def limpiar_archivo_ruta():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400

    archivo = request.files['archivo']
    if not archivo.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}), 400

    try:
        # Leer el archivo Excel subido
        df = pd.read_excel(archivo)

        # Leer los DataFrames adicionales desde uploads/Scorecard
        upload_dir = os.path.join('uploads', 'Scorecard')
        for file_name in ['Area-Equipo.xlsx', 'Inf Turnos.xlsx', 'T apertura.xlsx']:
            if not os.path.exists(os.path.join(upload_dir, file_name)):
                return jsonify({'error': f'El archivo {file_name} no se encuentra en {upload_dir}'}), 400
        dfAE = pd.read_excel(os.path.join(upload_dir, 'Area-Equipo.xlsx'))  
        InfTurnos = pd.read_excel(os.path.join(upload_dir, 'Inf Turnos.xlsx'))  
        dfTProd = pd.read_excel(os.path.join(upload_dir, 'T apertura.xlsx'))  

        # Aplicar funciones de limpieza
        dfl = modify_data(df)
        seglab, dfTecs, infTurnos, dfTProdAct, dfAEAct = Doc_Cleaned(dfl, dfAE, InfTurnos, dfTProd)

        # Crear un directorio temporal para el usuario
        temp_dir = tempfile.mkdtemp()
        dfs_limpios = {
            'seglab': seglab,
            'dfTecs': dfTecs,
            'infTurnos': infTurnos,
            'dfTProd': dfTProdAct,
            'dfAE': dfAEAct
        }

        # Guardar los DataFrames como archivos pickle en el directorio temporal
        session['dfs_limpios_paths'] = {}
        for key, df in dfs_limpios.items():
            temp_path = os.path.join(temp_dir, f'{key}.pkl')
            with open(temp_path, 'wb') as f:
                pickle.dump(df, f)
            session['dfs_limpios_paths'][key] = temp_path

        # Extraer semanas únicas de seglab
        if 'Semana' not in seglab.columns:
            return jsonify({'error': 'La columna "Semana" no existe en el archivo'}), 400
        semanas = seglab['Semana'].unique().tolist()
        return jsonify({'semanas': semanas})
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500

# Ruta para descargar una semana específica
@scorecard_bp.route('/descargar_semana', methods=['GET'])
def descargar_semana():
    if 'dfs_limpios_paths' not in session:
        return jsonify({'error': 'No hay datos limpios disponibles'}), 400

    semana = request.args.get('semana')
    if not semana:
        return jsonify({'error': 'No se especificó una semana'}), 400

    try:
        # Cargar los DataFrames desde los archivos pickle
        dfs_limpios = {}
        for key, path in session['dfs_limpios_paths'].items():
            with open(path, 'rb') as f:
                dfs_limpios[key] = pickle.load(f)

        # Filtrar seglab por semana
        seglab_filtrado = dfs_limpios['seglab'][dfs_limpios['seglab']['Semana'].astype(str) == str(semana)]
        if seglab_filtrado.empty:
            return jsonify({'error': f'No hay datos para la semana {semana}'}), 400

        # Crear un archivo Excel con todas las hojas
        output = BytesIO()
        with pd.ExcelWriter(output) as writer: 
            seglab_filtrado.to_excel(writer, sheet_name='Seg lab', index=False)
            dfs_limpios['dfTecs'].to_excel(writer, sheet_name='Tecnicos-Turnos', index=False)
            dfs_limpios['infTurnos'].to_excel(writer, sheet_name='Inf Turnos', index=False)
            dfs_limpios['dfTProd'].to_excel(writer, sheet_name='T apertura', index=False)
            dfs_limpios['dfAE'].to_excel(writer, sheet_name='Area-Equipo', index=False)
        output.seek(0)

        # Limpiar archivos temporales y sesión
        for path in session['dfs_limpios_paths'].values():
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(os.path.dirname(list(session['dfs_limpios_paths'].values())[0]))
        session.pop('dfs_limpios_paths', None)

        return send_file(output, download_name=f'SegLab_SEM{semana}.xlsx', as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Error al generar la descarga: {str(e)}'}), 500

# Ruta para descargar el archivo completo
@scorecard_bp.route('/descargar_completo', methods=['GET'])
def descargar_completo():
    if 'dfs_limpios_paths' not in session:
        return jsonify({'error': 'No hay datos limpios disponibles'}), 400

    try:
        # Cargar los DataFrames desde los archivos pickle
        dfs_limpios = {}
        for key, path in session['dfs_limpios_paths'].items():
            with open(path, 'rb') as f:
                dfs_limpios[key] = pickle.load(f)

        # Crear un archivo Excel con todas las hojas
        output = BytesIO()
        with pd.ExcelWriter(output) as writer:  
            dfs_limpios['seglab'].to_excel(writer, sheet_name='Seg lab', index=False)
            dfs_limpios['dfTecs'].to_excel(writer, sheet_name='Tecnicos-Turnos', index=False)
            dfs_limpios['infTurnos'].to_excel(writer, sheet_name='Inf Turnos', index=False)
            dfs_limpios['dfTProd'].to_excel(writer, sheet_name='T apertura', index=False)
            dfs_limpios['dfAE'].to_excel(writer, sheet_name='Area-Equipo', index=False)
        output.seek(0)

        # Limpiar archivos temporales y sesión
        for path in session['dfs_limpios_paths'].values():
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(os.path.dirname(list(session['dfs_limpios_paths'].values())[0]))
        session.pop('dfs_limpios_paths', None)

        return send_file(output, download_name='SegLab.xlsx', as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Error al generar la descarga: {str(e)}'}), 500


# RUTA PARA SUBIR BASE DE DATOS
@scorecard_bp.route('/subir_base_datos', methods=['POST'])
def subir_base_datos():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400

    archivo = request.files['archivo']
    if not archivo.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}), 400

    try:
        # Crear la carpeta uploads/Scorecard si no existe
        upload_dir = os.path.join('Uploads', 'Scorecard')
        os.makedirs(upload_dir, exist_ok=True)
        # Leer el archivo Excel subido
        xl = pd.ExcelFile(archivo)
        # Verificar que las hojas esperadas existan
        required_sheets = ['Seg lab', 'Tecnicos-Turnos', 'Inf Turnos', 'T apertura', 'Area-Equipo']
        missing_sheets = [sheet for sheet in required_sheets if sheet not in xl.sheet_names]
        if missing_sheets:
            return jsonify({'error': f'Faltan las hojas: {", ".join(missing_sheets)}'}), 400
        # Leer las hojas como DataFrames
        seglab = pd.read_excel(archivo, sheet_name='Seg lab')
        Tec_Tur = pd.read_excel(archivo, sheet_name='Tecnicos-Turnos')
        InfTurnos = pd.read_excel(archivo, sheet_name='Inf Turnos')
        dfTProd = pd.read_excel(archivo, sheet_name='T apertura')
        dfAEAct = pd.read_excel(archivo, sheet_name='Area-Equipo')

        # Aplicar validaciones y limpieza
        seglab['Minutos'] = pd.to_numeric(seglab['Minutos'], errors='coerce').fillna(0).astype(float)
        Tec_Tur['Turno'] = Tec_Tur['Turno'].apply(lambda x: x if x in [1, 2, 3, 4, "mix"] else "N A")
        Tec_Tur['Turno'] = Tec_Tur['Turno'].apply(lambda x: int(x) if isinstance(x, (int, float)) and x in [1, 2, 3, 4] else x)
        dfTProd["T apertura (ajustar si es necesario)"] = pd.to_numeric(
            dfTProd["T apertura (ajustar si es necesario)"], errors='coerce'
        ).fillna(8064).astype(float)
        dfAEAct.drop_duplicates(subset='SAP', keep='first', inplace=True)

        # Obtener el año actual y filtrar seglab por semanas del año actual
        añoAct = datetime.datetime.now().year
        seglab = seglab.loc[seglab['Fecha'].dt.isocalendar().year == añoAct].reset_index(drop=True)

        # Asegurar que Fecha sea datetime
        seglab['Fecha'] = pd.to_datetime(seglab['Fecha'], errors='coerce')
        if seglab['Fecha'].isna().any():
            return jsonify({'error': 'Algunas fechas en la columna Fecha de Seg lab no son válidas'}), 400

        # Guardar cada DataFrame como un archivo Excel separado
        dataframes = {
            'Seg lab': seglab,
            'Tecnicos-Turnos': Tec_Tur,
            'Inf Turnos': InfTurnos,
            'T apertura': dfTProd,
            'Area-Equipo': dfAEAct
        }

        for sheet_name, df in dataframes.items():
            output_path = os.path.join(upload_dir, f'{sheet_name}.xlsx')
            df.to_excel(output_path, index=False)


        return jsonify({'mensaje': 'Base de datos subida y guardada correctamente, puedes acceder a tus indicadores'})
    except Exception as e:
        return jsonify({'error': f'Error al procesar la base de datos: {str(e)}'}), 500
    
    
# *************************************** INDICADORES ***************************************************

@scorecard_bp.route('/process_filters', methods=['POST'])
def process_filters():
    data = request.get_json()
    uap = data.get('uap')
    week = int(data.get('week'))  # Convertir a entero

    # Validar entradas
    load_dataframes()
    if (uap not in UAP_OPTIONS or 
        DATA_CACHE['seglab'] is None or 
        week not in DATA_CACHE['seglab']['Semana'].unique()):
        return jsonify({'error': 'UAP o semana inválida'}), 400

    # Verificar caché de UAP_SCR
    cache_key = f"{uap}_{week}"
    if cache_key in UAP_SCR_CACHE:
        df_list, fig_list, fig0_path, temp_dir = UAP_SCR_CACHE[cache_key]
        # Verificar si los archivos aún existen
        if os.path.exists(fig0_path) and os.path.exists(os.path.join(temp_dir, 'df_list.pkl')) and os.path.exists(os.path.join(temp_dir, 'fig_list.pkl')):
            print(f"Usando caché para uap={uap}, week={week}")
        else:
            print(f"Caché inválido para uap={uap}, week={week}, regenerando datos")
            # Limpiar entrada inválida del caché
            try:
                if os.path.exists(fig0_path):
                    os.remove(fig0_path)
                if os.path.exists(os.path.join(temp_dir, 'df_list.pkl')):
                    os.remove(os.path.join(temp_dir, 'df_list.pkl'))
                if os.path.exists(os.path.join(temp_dir, 'fig_list.pkl')):
                    os.remove(os.path.join(temp_dir, 'fig_list.pkl'))
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"Error al limpiar caché inválido {temp_dir}: {e}")
            del UAP_SCR_CACHE[cache_key]
            df_list, fig_list, fig0_path, temp_dir = None, None, None, None

    if cache_key not in UAP_SCR_CACHE:
        # Cargar DataFrames desde caché
        seglab = DATA_CACHE['seglab']
        seglabSP = seglab[seglab['Semana'] == week]
        tec_tur = DATA_CACHE['tec_tur']
        inf_turnos = DATA_CACHE['inf_turnos']
        df_tprod = DATA_CACHE['df_tprod']

        # Llamar a la función UAP_SCR
        try:
            df_list, fig_list = UAP_SCR(seglab, seglabSP, uap, UAP_OPTIONS[uap], tec_tur, inf_turnos, df_tprod, week)
        except Exception as e:
            return jsonify({'error': f'Error en UAP_SCR: {e}'}), 500

        # Crear un directorio temporal único para esta combinación
        temp_dir = os.path.join(tempfile.gettempdir(), f"scorecard_{uap}_{week}")
        os.makedirs(temp_dir, exist_ok=True)
        df_list_path = os.path.join(temp_dir, 'df_list.pkl')
        fig_list_path = os.path.join(temp_dir, 'fig_list.pkl')
        fig0_path = os.path.join(temp_dir, 'fig0.png')

        # Guardar df_list, fig_list y la primera figura como archivos
        try:
            with open(df_list_path, 'wb') as f:
                pickle.dump(df_list, f)
            with open(fig_list_path, 'wb') as f:
                pickle.dump(fig_list, f)
            # Guardar la primera figura como PNG
            with open(fig0_path, 'wb') as f:
                fig_list[0].savefig(f, format='png', bbox_inches='tight', dpi=100)
        except Exception as e:
            print(f"Error al guardar archivos temporales: {e}")
            return jsonify({'error': f'Error al guardar datos temporales: {e}'}), 500
        finally:
            # Cerrar todas las figuras para liberar memoria
            for fig in fig_list:
                plt.close(fig)

        # Almacenar en caché
        UAP_SCR_CACHE[cache_key] = (df_list, fig_list, fig0_path, temp_dir)

    # Guardar las rutas en la sesión
    session['temp_dir'] = temp_dir
    session['df_list_path'] = os.path.join(temp_dir, 'df_list.pkl')
    session['fig_list_path'] = os.path.join(temp_dir, 'fig_list.pkl')
    session['fig0_path'] = fig0_path
    session['uap'] = uap
    session['week'] = week

    # Leer la primera figura desde el archivo
    try:
        with open(fig0_path, 'rb') as f:
            fig_data = f.read()
    except Exception as e:
        print(f"Error al leer fig0_path: {e}")
        return jsonify({'error': 'Error al cargar la imagen'}), 500

    # Convertir la imagen a base64
    import base64
    fig_base64 = base64.b64encode(fig_data).decode('utf-8')

    return jsonify({'image': fig_base64})

@scorecard_bp.route('/download_excel', methods=['GET'])
def download_excel():
    if 'df_list_path' not in session or not os.path.exists(session.get('df_list_path', '')):
        print("Error: No hay df_list_path en la sesión o el archivo no existe")
        return jsonify({'error': 'No hay datos disponibles. Por favor, selecciona los filtros nuevamente.'}), 400

    try:
        with open(session['df_list_path'], 'rb') as f:
            df_list = pickle.load(f)
    except Exception as e:
        print(f"Error al cargar df_list desde archivo: {e}")
        return jsonify({'error': 'Error al cargar datos'}), 500

    uap = session.get('uap', 'unknown')
    week = session.get('week', 'unknown')

    # Optimizar DataFrames: eliminar columnas vacías
    df_list = [df.dropna(how='all', axis=1) for df in df_list]

    # Crear un DataFrame vacío si la lista está vacía
    if not df_list:
        print("Advertencia: df_list está vacío, generando Excel con hojas vacías")
        df_list = [pd.DataFrame() for _ in range(9)]  # Crear 9 DataFrames vacíos

    # Nombres de las hojas
    sheet_names = ['GENERAL', 'AVERIAS', 'MENSUAL', 'SEMANAL', 'MTBF', 'MTTR', 'TECNICOS', 'PREV ACUMULADO', 'PREV SEMANA']

    # Crear el archivo Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for df, sheet_name in zip(df_list, sheet_names):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'Scorecard_{uap}_Semana{week}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@scorecard_bp.route('/download_pdf', methods=['GET'])
def download_pdf():
    if 'fig_list_path' not in session or not os.path.exists(session.get('fig_list_path', '')):
        print("Error: No hay fig_list_path en la sesión o el archivo no existe")
        return jsonify({'error': 'No hay figuras disponibles. Por favor, selecciona los filtros nuevamente.'}), 400

    try:
        with open(session['fig_list_path'], 'rb') as f:
            fig_list = pickle.load(f)
    except Exception as e:
        print(f"Error al cargar fig_list desde archivo: {e}")
        return jsonify({'error': 'Error al cargar figuras'}), 500

    uap = session.get('uap', 'unknown')
    week = session.get('week', 'unknown')

    # Crear una figura vacía si la lista está vacía
    if not fig_list:
        print("Advertencia: fig_list está vacío, generando PDF con una figura vacía")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No hay datos disponibles', ha='center', va='center')
        fig_list = [fig]

    # Crear el archivo PDF
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        for fig in fig_list:
            pdf.savefig(fig, bbox_inches='tight', dpi=100)
            plt.close(fig)  # Cerrar figura para liberar memoria
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'Scorecard_{uap}_Semana{week}.pdf',
        mimetype='application/pdf'
    )