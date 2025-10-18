import pandas as pd
import joblib
import numpy as np

def preprocess_input(input_data, model_path='Predictores/modelXGB/'):
    """
    Preprocesa los datos de entrada para el modelo de tiempo de paro.
    
    Args:
        input_data (dict): Diccionario con las entradas del formulario
        model_path (str): Ruta al directorio con los objetos serializados
    
    Returns:
        pd.DataFrame: Datos preprocesados listos para el modelo
    """
    # Cargar objetos de preprocesamiento
    ordinal_encoder = joblib.load(f'{model_path}ordinal_encoder.joblib')
    target_encoder = joblib.load(f'{model_path}target_encoder.joblib')
    scaler_lprev = joblib.load(f'{model_path}scaler_lprev.joblib')
    scaler_prevs_period = joblib.load(f'{model_path}scaler_prevs_period.joblib')
    scaler_avs_period = joblib.load(f'{model_path}scaler_avs_period.joblib')
    lprev_medians = joblib.load(f'{model_path}lprev_medians.joblib')
    
    # Convertir entrada a DataFrame
    data = pd.DataFrame([input_data])

    # Imputar LPrev
    lprev_default = lprev_medians.get(data['IDMaquina'].iloc[0], lprev_medians.median())
    data['LPrev'] = data.apply(
        lambda x: lprev_medians.get(x['IDMaquina'], lprev_default) if pd.isna(x['LPrev']) else x['LPrev'], 
        axis=1
    ).fillna(lprev_default)
    
    # Usar columnas definidas en los codificadores entrenados
    ordinal_cols = ordinal_encoder.cols
    target_cols = target_encoder.cols
 
    # Codificación categórica
    data_encoded = data.copy()
    
    # Aplicar OrdinalEncoder
    if ordinal_cols:
        ordinal_encoded = pd.DataFrame(
            ordinal_encoder.transform(data[ordinal_cols]),
            columns=ordinal_cols,
            index=data.index
        )
        data_encoded[ordinal_cols] = ordinal_encoded
    
    # Aplicar TargetEncoder
    if target_cols:
        target_encoded = pd.DataFrame(
            target_encoder.transform(data[target_cols]),
            columns=target_cols,
            index=data.index
        )
        data_encoded[target_cols] = target_encoded
    
    # Escalado numérico
    data_scaled = data_encoded.copy()
    
    # LPrev
    data_scaled['LPrev'] = np.log1p(data_scaled['LPrev']).astype(np.float64)
    data_scaled['LPrev'] = scaler_lprev.transform(data_scaled[['LPrev']]).astype(np.float64)
    
    # Prevs_period
    data_scaled['Prevs_period'] = np.log1p(data_scaled['Prevs_period']).astype(np.float64)
    data_scaled['Prevs_period'] = scaler_prevs_period.transform(data_scaled[['Prevs_period']]).astype(np.float64)
    
    # Avs_period
    data_scaled['Avs_period'] = np.log1p(data_scaled['Avs_period']).astype(np.float64)
    data_scaled['Avs_period'] = scaler_avs_period.transform(data_scaled[['Avs_period']]).astype(np.float64)
    
    # Prioridad
    data_scaled['Prioridad'] = ((data_scaled['Prioridad'] - 1) / 2).astype(np.float64)
    
    # Semana cíclica
    data_scaled['Semana_sin'] = np.sin(2 * np.pi * (data_scaled['Semana'] - 1) / 52).astype(np.float64)
    data_scaled['Semana_cos'] = np.cos(2 * np.pi * (data_scaled['Semana'] - 1) / 52).astype(np.float64)
    data_scaled = data_scaled.drop('Semana', axis=1)
    
    # Hora cíclica
    data_scaled['Hora_sin'] = np.sin(2 * np.pi * data_scaled['Hora'] / 24).astype(np.float64)
    data_scaled['Hora_cos'] = np.cos(2 * np.pi * data_scaled['Hora'] / 24).astype(np.float64)
    data_scaled = data_scaled.drop('Hora', axis=1)
 
    
    # Eliminar columnas innecesarias
    data_scaled = data_scaled.drop(columns=['Prevs', 'Avs'], errors='ignore')
    
    # Ordenar columnas según el modelo
    feature_names = [
        'IDMaquina', 'Dia', 'Mes', 'Tipo', 'Prioridad', 'UAP', 'Tecnico',
        'LPrev', 'Prevs_period', 'Avs_period', 'Semana_sin', 'Semana_cos',
        'Hora_sin', 'Hora_cos'
    ]
    data_scaled = data_scaled[feature_names]
    
    return data_scaled


def postprocess_output(prediction, model_path='Predictores/modelXGB/'):
    """
    Revierte las transformaciones de la predicción para obtener minutos reales.
    
    Args:
        prediction (np.ndarray): Predicción del modelo (escalada)
        model_path (str): Ruta al directorio con los objetos serializados
    
    Returns:
        float: Predicción en minutos reales
    """
    scaler_minutos = joblib.load(f'{model_path}scaler_minutos.joblib')
    upper_limit = joblib.load(f'{model_path}upper_limit.joblib')
    lower_limit = 5  # Límite inferior
    
    # Revertir escalado y transformación logarítmica
    pred_unscaled = scaler_minutos.inverse_transform(prediction.reshape(-1, 1)).flatten()
    pred_minutes = np.expm1(pred_unscaled)
    
    # Aplicar límites
    pred_minutes = np.clip(pred_minutes, lower_limit, upper_limit)
    
    return pred_minutes[0]