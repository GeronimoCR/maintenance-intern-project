import pandas as pd
import numpy as np
import joblib

def preprocess_inputN(input_data, model_path='Predictores/modelNParo/'):
    """
    Preprocesa los datos de entrada para el modelo de NParo.
    
    Args:
        input_data (dict): Diccionario con las entradas del formulario
        model_path (str): Ruta al directorio con los objetos serializados
    
    Returns:
        pd.DataFrame: Datos preprocesados listos para el modelo
    """
    # Cargar objetos de preprocesamiento
    target_encoders = {
        col: joblib.load(f'{model_path}target_encoder_{col}.joblib')
        for col in ['Maquina', 'Mes', 'Tecnico']  # Ajusta según high_cardinality_cols
    }
    ordinal_encoder = joblib.load(f'{model_path}ordinal_encoder.joblib')
    scalers = {
        'scalerlav': joblib.load(f'{model_path}scaler_lav.joblib'),
        'scalerlprev': joblib.load(f'{model_path}scaler_lprev.joblib'),
        'scalerlimp': joblib.load(f'{model_path}scaler_limp.joblib'),
        'scaler_noprev': joblib.load(f'{model_path}scaler_noprev.joblib'),
        'scaler_noav': joblib.load(f'{model_path}scaler_noav.joblib'),
        'scaler_noimp': joblib.load(f'{model_path}scaler_noimp.joblib'),
        'scaler_prior': joblib.load(f'{model_path}scaler_prior.joblib')
    }
    winsor_limits = joblib.load(f'{model_path}winsor_limits.joblib')
    
    # Convertir entrada a DataFrame
    data = pd.DataFrame([input_data])
    
    # Definir columnas
    feature_cols = ['Maquina', 'Dia', 'Mes', 'Hora', 'Semana', 'Tipo', 'Prior', 'UAP', 'Tecnico', 
                    'L Av', 'L Prev', 'L Imp', 'NoPrev 3m', 'NoAv 3m', 'NoImp 3m']
    categorical_cols = ['Maquina', 'Dia', 'Mes', 'Tipo', 'UAP', 'Tecnico']
    numeric_cols = ['L Av', 'L Prev', 'L Imp', 'NoPrev 3m', 'NoAv 3m', 'NoImp 3m', 'Prior', 
                    'Semana_sin', 'Semana_cos', 'Hora_sin', 'Hora_cos']
    
    # Asegurar que todas las columnas necesarias estén presentes
    data = data[feature_cols]
    
    # --- Transformaciones numéricas ---
    # Recorte con np.clip
    for col in ['L Av', 'L Prev', 'L Imp', 'NoPrev 3m', 'NoAv 3m', 'NoImp 3m']:
        lower_bound, upper_bound = winsor_limits[col]
        data[col] = np.clip(data[col], lower_bound, upper_bound)
    
    # Transformación logarítmica
    for col in ['L Av', 'L Prev', 'L Imp', 'NoPrev 3m', 'NoAv 3m', 'NoImp 3m']:
        data[col] = np.log1p(data[col])
    
    # Estandarización
    data['L Av'] = scalers['scalerlav'].transform(data[['L Av']])
    data['L Prev'] = scalers['scalerlprev'].transform(data[['L Prev']])
    data['L Imp'] = scalers['scalerlimp'].transform(data[['L Imp']])
    data['NoPrev 3m'] = scalers['scaler_noprev'].transform(data[['NoPrev 3m']])
    data['NoAv 3m'] = scalers['scaler_noav'].transform(data[['NoAv 3m']])
    data['NoImp 3m'] = scalers['scaler_noimp'].transform(data[['NoImp 3m']])
    data['Prior'] = scalers['scaler_prior'].transform(data[['Prior']])
    
    # Transformaciones cíclicas
    data['Semana_sin'] = np.sin(2 * np.pi * (data['Semana'] - 1) / 52).astype(np.float64)
    data['Semana_cos'] = np.cos(2 * np.pi * (data['Semana'] - 1) / 52).astype(np.float64)
    data['Hora_sin'] = np.sin(2 * np.pi * data['Hora'] / 24).astype(np.float64)
    data['Hora_cos'] = np.cos(2 * np.pi * data['Hora'] / 24).astype(np.float64)
    
    # Eliminar columnas originales
    data = data.drop(['Semana', 'Hora'], axis=1)
    
    # --- Codificación categórica ---
    # Target Encoding para columnas de alta cardinalidad
    high_cardinality_cols = ['Maquina', 'Mes', 'Tecnico']  
    for col in high_cardinality_cols:
        if col in target_encoders:
            data[col] = target_encoders[col].transform(data[[col]])
    
    # Ordinal Encoding para columnas de baja cardinalidad
    low_cardinality_cols = ['Dia', 'Tipo', 'UAP']  
    if low_cardinality_cols:
        data[low_cardinality_cols] = ordinal_encoder.transform(data[low_cardinality_cols])
    
    # Ordenar columnas según el modelo
    data = data[categorical_cols + numeric_cols]
    
    return data

def postprocess_outputN(prediction, model_path='Predictores/modelNParo/'):
    """
    Revierte las transformaciones de la predicción para obtener minutos reales.
    
    Args:
        prediction (np.ndarray): Predicción del modelo (escalada)
        model_path (str): Ruta al directorio con los objetos serializados
    
    Returns:
        float: Predicción en minutos reales
    """
    scaler_nxtav = joblib.load(f'{model_path}scaler_nxtav.joblib')
    winsor_limits = joblib.load(f'{model_path}winsor_limits.joblib')
    upper_limit = winsor_limits['Nxt Av']  # Límite superior para Nxt Av
    
    # Revertir escalado y transformación logarítmica
    pred_unscaled = scaler_nxtav.inverse_transform(prediction.reshape(-1, 1)).flatten()
    pred_minutes = np.expm1(pred_unscaled)
    
    # Aplicar límite superior
    pred_minutes = np.clip(pred_minutes, 0, upper_limit)
    
    return pred_minutes[0]