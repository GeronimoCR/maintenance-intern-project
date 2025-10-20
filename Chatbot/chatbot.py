from flask import Blueprint, request, jsonify, render_template
from transformers import TFBertForSequenceClassification, BertTokenizer
import tensorflow as tf
import json
import pandas as pd
import os
import gdown

# Crear blueprint
chatbot_bp = Blueprint('chatbot', __name__, template_folder='../templates', static_folder='../static')

def load_chatbot_model():
    model_path = os.path.join(os.path.dirname(__file__), 'chatbot_model')
    if not os.path.exists(model_path):
        gdown.download_folder('https://drive.google.com/drive/folders/1Z8TXHT75u5qpS--JZvBWSAw9rZZjK6N8?usp=drive_link', output=model_path, quiet=False)
    model = TFBertForSequenceClassification.from_pretrained(model_path)
    tokenizer = BertTokenizer.from_pretrained(model_path)

    # Cargar diccionario
    with open(os.path.join(model_path, 'label_to_intent.json'), 'r') as f:
        label_to_intent = json.load(f)
    # Cargar respuestas
    respuestas_path = os.path.join(model_path, 'respuestas.xlsx')  # Ahora está en chatbot_model/
    respuestas_df = pd.read_excel(respuestas_path)
    respuestas_dict = dict(zip(respuestas_df['Intención'], respuestas_df['Respuesta']))
    return model, tokenizer, label_to_intent, respuestas_dict

# Función para predecir intención
def predecir_intencion(pregunta, model, tokenizer, label_to_intent, respuestas_dict):
    inputs = tokenizer(pregunta, truncation=True, padding=True, max_length=128, return_tensors='tf')
    outputs = model(inputs)
    logits = outputs.logits
    pred_label = tf.argmax(tf.nn.softmax(logits, axis=-1), axis=-1).numpy()[0]
    intencion = label_to_intent[str(pred_label)]
    respuesta = respuestas_dict.get(intencion, 'No entendí lo que acaba de preguntar, le agradecería reformular su pregunta de manera más específica. En caso de que aún carezca de información disponible le aconsejo preguntar al personal encargado o consultar en las ventanas de "Ayuda" presentes en las páginas del sitio.')
    return respuesta, intencion

@chatbot_bp.route('/', methods=['POST'])
def chatbot():
    model, tokenizer, label_to_intent, respuestas_dict = load_chatbot_model()
    data = request.json
    pregunta = data.get('pregunta', '')
    respuesta, intencion = predecir_intencion(pregunta, model, tokenizer, label_to_intent, respuestas_dict)
    return jsonify({'respuesta': respuesta, 'intencion': intencion})

@chatbot_bp.route('/predict', methods=['POST'])
def predict():
    model, tokenizer, label_to_intent, respuestas_dict = load_chatbot_model()
    data = request.json
    pregunta = data.get('pregunta', '')
    respuesta, intencion = predecir_intencion(pregunta, model, tokenizer, label_to_intent, respuestas_dict)
    return jsonify({'respuesta': respuesta, 'intencion': intencion})