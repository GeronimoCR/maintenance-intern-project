from flask import Flask, render_template
from Monitoreo_Energetico.Monitoreo_Energetico import monitoreo_bp
from PDFprev.PDFprev import PDFprev_bp
from Scorecard.Scorecard import scorecard_bp
from Analisis_Energetico.Analisis_Energetico import analisisE_bp
from Predictores.Predictores import predictores_bp
from Chatbot.chatbot import chatbot_bp
from waitress import serve


app = Flask(__name__)

app.secret_key = 'd390e3824fc22f6f5acb98fd0910c9da9acd80ec46b2b7e0'
#BLUEPRINTS (Diversos modulos para las diversas funciones)
app.register_blueprint(monitoreo_bp, url_prefix='/Monitoreo_Energetico')
app.register_blueprint(PDFprev_bp, url_prefix='/PDFprev')
app.register_blueprint(scorecard_bp, url_prefix='/Scorecard')
app.register_blueprint(predictores_bp, url_prefix='/Predictores')
app.register_blueprint(analisisE_bp, url_prefix='/AnalisisE')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')


#RUTA DE INDICE PRINCIPAL
@app.route('/')
def index():
    return render_template('index.html')


import os
if os.environ.get("FLY_APP_NAME"):
    import threading
    import time
    from waitress import serve

    # 1. SERVIDOR FALSO que responde en 1 segundo
    def fake_server():
        from flask import Flask
        fake = Flask(__name__)
        @fake.route('/')
        def health(): return 'OK', 200
        serve(fake, host='0.0.0.0', port=8080, threads=1)

    # 2. Lo lanza en un hilo para que Fly vea el puerto YA
    threading.Thread(target=fake_server, daemon=True).start()
    print("Salud falsa activada en 0.0.0.0:8080")

    # 3. TE DA 35 SEGUNDOS para que carguen tus modelos ML
    print("Cargando modelos pesados… (35 seg)")
    time.sleep(35)

    # 4. AHORA SÍ arranca el servidor REAL
    print("¡TODO LISTO! Sirviendo tu app real")
    serve(app, host="0.0.0.0", port=8080, threads=6)


