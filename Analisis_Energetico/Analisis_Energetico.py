from flask import Blueprint, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
from .AnalisisE_lib import DataGral, DataUAP, DataNave_Wknd
import os
import base64
import matplotlib.pyplot as plt
import io
import tempfile

analisisE_bp = Blueprint('analisisE', __name__, template_folder='../Templates', static_folder='../static')
CORS(analisisE_bp)

# Almacenar archivos temporales por sesión (usando IP como identificador)
temp_files1 = {} #Actualice el niombre del diccionario para separar lo de una pagina de la otra
temp_files2 = {} #Nuevo diccionario para hacer algo parecido con la nueva ruta

@analisisE_bp.route('/AnalisisMain')
def AnalisisMain():
    return render_template('Monitoreo/AnalisisMain.html')

@analisisE_bp.route('/AnalisisMen')
def AnalisisMen():
    return render_template('Monitoreo/AnalisisMen.html')

@analisisE_bp.route('/AnalisisWknd')
def AnalisisWknd():
    return render_template('Monitoreo/AnalisisWknd.html')

@analisisE_bp.route('/upload_file', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        session_id = request.remote_addr
        
        # Guardar archivo temporalmente
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{session_id}_{file.filename}")
        file.save(temp_path)
        
        # Leer hojas y guardar en memoria
        dfMeds = pd.read_excel(temp_path, sheet_name='Datos horarios')
        EqUAPs = pd.read_excel(temp_path, sheet_name='MaquinaUAP')
        temp_files1[session_id] = {'path': temp_path, 'dfMeds': dfMeds, 'EqUAPs': EqUAPs}

        # Obtener UAPs únicas
        uaps = list(EqUAPs.UAP.unique())
        
        # Procesar datos generales
        df_gral, fig_gral = DataGral(dfMeds, EqUAPs)
        
        # Convertir figura a base64
        buffer = io.BytesIO()
        fig_gral.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig_gral)
        
        # Convertir DataFrame a Excel
        excel_buffer = io.BytesIO()
        df_gral.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_base64 = base64.b64encode(excel_buffer.getvalue()).decode()
        
        return jsonify({
            'image': image_base64,
            'excel_data': excel_base64,
            'uaps': uaps
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@analisisE_bp.route('/filter_data', methods=['POST'])
def filter_data():
    try:
        
        data = request.get_json()
        uap = data['uap']
        session_id = request.remote_addr
        
        if session_id not in temp_files1:
            return jsonify({'error': 'No se ha subido ningún archivo'}), 400
        
        # Usar DataFrames en memoria
        dfMeds = temp_files1[session_id]['dfMeds']
        EqUAPs = temp_files1[session_id]['EqUAPs']
        
        # Procesar datos
        if uap == 'General':
            df_result, fig_result = DataGral(dfMeds, EqUAPs)
        else:
            df_result, fig_result = DataUAP(dfMeds, EqUAPs, uap)

        
        # Convertir figura a base64
        buffer = io.BytesIO()
        fig_result.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig_result)
        
        # Convertir DataFrame a Excel
        excel_buffer = io.BytesIO()
        df_result.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_base64 = base64.b64encode(excel_buffer.getvalue()).decode()
        
        return jsonify({
            'image': image_base64,
            'excel_data': excel_base64
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Rutas para AnalisisWknd
@analisisE_bp.route('/upload_file_wknd', methods=['POST'])
def upload_file_wknd():
    try:
        file = request.files['file']
        session_id = request.remote_addr
        
        # Guardar archivo temporalmente
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{session_id}_wknd_{file.filename}")
        file.save(temp_path)
        
        # Leer hojas y guardar en memoria
        dfMeds = pd.read_excel(temp_path, sheet_name='Datos horarios')
        EqUAPs = pd.read_excel(temp_path, sheet_name='MaquinaUAP')
        MedNav = pd.read_excel(temp_path, sheet_name='MedidoresNave')
        temp_files2[session_id] = {
            'path': temp_path,
            'dfMeds': dfMeds,
            'EqUAPs': EqUAPs,
            'MedNav': MedNav
        }

        # Obtener Naves únicas
        naves = list(MedNav['Nave'].unique())
        
        return jsonify({
            'naves': naves
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@analisisE_bp.route('/filter_data_wknd', methods=['POST'])
def filter_data_wknd():
    try:
        data = request.get_json()
        nave = data['nave']
        session_id = request.remote_addr
        
        if session_id not in temp_files2:
            return jsonify({'error': 'No se ha subido ningún archivo'}), 400
        
        # Usar DataFrames en memoria
        dfMeds = temp_files2[session_id]['dfMeds']
        EqUAPs = temp_files2[session_id]['EqUAPs']
        MedNav = temp_files2[session_id]['MedNav']
        
        # Procesar datos
        df_result, fig_result, period_start, period_end = DataNave_Wknd(dfMeds, MedNav, EqUAPs, nave)
        
        # Convertir figura a base64
        buffer = io.BytesIO()
        fig_result.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig_result)
        
        # Convertir DataFrame a Excel
        excel_buffer = io.BytesIO()
        df_result.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_base64 = base64.b64encode(excel_buffer.getvalue()).decode()
        
        return jsonify({
            'image': image_base64,
            'excel_data': excel_base64,
            'period_start': period_start,
            'period_end': period_end
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@analisisE_bp.route('/logout', methods=['POST'])
def logout():
    session_id = request.remote_addr
    # Limpiar temp_files1 (AnalisisMen)
    if session_id in temp_files1:
        try:
            os.remove(temp_files1[session_id]['path'])
            del temp_files1[session_id]
        except:
            pass
    # Limpiar temp_files2 (AnalisisWknd)
    if session_id in temp_files2:
        try:
            os.remove(temp_files2[session_id]['path'])
            del temp_files2[session_id]
        except:
            pass
    return jsonify({'status': 'success'})