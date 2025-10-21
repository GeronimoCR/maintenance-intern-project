from flask import Blueprint, request, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import gdown
import os
from .PreprocessingTParo import preprocess_input, postprocess_output
from .PreprocessingNParo import preprocess_inputN, postprocess_outputN

predictores_bp = Blueprint('predictores', __name__, template_folder='templates', static_folder='static')
CORS(predictores_bp)

categorical_cols = ['IDMaquina', 'Dia', 'Mes', 'UAP', 'Tipo', 'Tecnico']
nparo_categorical_cols = ['Maquina', 'Dia', 'Mes', 'Tipo', 'UAP', 'Tecnico']


def load_tparo_resources():
    model_path = os.path.join(os.path.dirname(__file__), 'modelTParo')
    if not os.path.exists(model_path):
        gdown.download_folder('https://drive.google.com/drive/folders/1tw6eEq6zxwswq_blIzU19cKSV3bYzH-q', output=model_path, quiet=False)
    valid_values = {col: joblib.load(f'{model_path}/valid_{col}.joblib').tolist() if isinstance(joblib.load(f'{model_path}/valid_{col}.joblib'), np.ndarray) else joblib.load(f'{model_path}/valid_{col}.joblib') for col in categorical_cols}
    return valid_values, model_path

def load_nparo_resources():
    model_path = os.path.join(os.path.dirname(__file__), 'modelNParo')
    if not os.path.exists(model_path):
        gdown.download_folder('https://drive.google.com/drive/folders/1E0rLZUDS_j8eSn5AKeImYJ-UxB-B2ak-', output=model_path, quiet=False)
    valid_values = {col: joblib.load(f'{model_path}/valid_{col}.joblib') for col in nparo_categorical_cols}
    return valid_values, model_path

@predictores_bp.route('/TParo', methods=['GET', 'POST'])
def TParo():
    valid_values, model_path = load_tparo_resources()
    if request.method == 'POST':
        try:
            input_data = {
                'IDMaquina': request.form['IDMaquina'],
                'Dia': request.form['Dia'],
                'Mes': request.form['Mes'],
                'Hora': int(request.form['Hora']),
                'Semana': int(request.form['Semana']),
                'Tipo': request.form['Tipo'],
                'Prioridad': int(request.form['Prioridad']),
                'UAP': request.form['UAP'],
                'Tecnico': request.form['Tecnico'],
                'Prevs_period': float(request.form['Prevs_period']),
                'Avs_period': float(request.form['Avs_period']),
                'LPrev': float(request.form['LPrev'])
            }

            for col in categorical_cols:
                if input_data[col] not in valid_values[col]:
                    error_message = f"El valor '{input_data[col]}' para {col} no es válido."
                    print("Error de validación:", error_message)
                    return render_template('Predictores/TParo.html', 
                                         valid_values=valid_values, 
                                         error_message=error_message)

            data_processed = preprocess_input(input_data, model_path=model_path)
            xgb_model = joblib.load(f'{model_path}/xgb_tiempo_paro_model.joblib')
            prediction = xgb_model.predict(data_processed)
            result = postprocess_output(prediction, model_path=model_path)
            
            return render_template('Predictores/TParo.html', 
                                 valid_values=valid_values, 
                                 prediction=round(result, 2))

        except (ValueError, KeyError) as e:
            error_message = f"Error en los datos ingresados: {str(e)}"
            print("Excepción:", error_message)
            return render_template('Predictores/TParo.html', 
                                 valid_values=valid_values, 
                                 error_message=error_message)

    return render_template('Predictores/TParo.html', valid_values=valid_values)

@predictores_bp.route('/NParo', methods=['GET', 'POST'])
def nparo():
    valid_values, model_path = load_nparo_resources()
    if request.method == 'POST':
        try:
            input_data = {
                'Maquina': request.form['Maquina'],
                'Dia': request.form['Dia'],
                'Mes': request.form['Mes'],
                'Hora': float(request.form['Hora']),
                'Semana': float(request.form['Semana']),
                'Tipo': request.form['Tipo'],
                'Prior': float(request.form['Prior']),
                'UAP': request.form['UAP'],
                'Tecnico': request.form['Tecnico'],
                'L Av': float(request.form['L_Av']),
                'L Prev': float(request.form['L_Prev']),
                'L Imp': float(request.form['L_Imp']),
                'NoPrev 3m': float(request.form['NoPrev_3m']),
                'NoAv 3m': float(request.form['NoAv_3m']),
                'NoImp 3m': float(request.form['NoImp_3m'])
            }
            
            for col in nparo_categorical_cols:
                if input_data[col] not in valid_values[col]:
                    error_message = f"El valor '{input_data[col]}' para {col} no es válido."
                    print("Error de validación:", error_message)
                    return render_template('Predictores/NParo.html', 
                                        valid_values=valid_values, 
                                        error_message=error_message)
            
            data_processed = preprocess_inputN(input_data, model_path=model_path)
            model = joblib.load(f'{model_path}/xgb_nparo_model.joblib')
            prediction = model.predict(data_processed)
            result = postprocess_outputN(prediction, model_path=model_path)
            
            return render_template('Predictores/NParo.html', 
                                valid_values=valid_values, 
                                prediction=round(result, 2))
        
        except (ValueError, KeyError) as e:
            error_message = f"Error en los datos ingresados: {str(e)}"
            print("Excepción:", error_message)
            return render_template('Predictores/NParo.html', 
                                valid_values=valid_values, 
                                error_message=error_message)
    
    return render_template('Predictores/NParo.html', valid_values=valid_values)

@predictores_bp.route('/PredictoresMain')
def PMain():
    return render_template('Predictores/PredictoresMain.html')