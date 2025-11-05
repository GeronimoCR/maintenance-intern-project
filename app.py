from flask import Flask, render_template
from Monitoreo_Energetico.Monitoreo_Energetico import monitoreo_bp
from PDFprev.PDFprev import PDFprev_bp
from Scorecard.Scorecard import scorecard_bp
from Analisis_Energetico.Analisis_Energetico import analisisE_bp
from Predictores.Predictores import predictores_bp
from Chatbot.chatbot import chatbot_bp

app = Flask(__name__)
app.secret_key = 'd390e3824fc22f6f5acb98fd0910c9da9acd80ec46b2b7e0'

# BLUEPRINTS
app.register_blueprint(monitoreo_bp, url_prefix='/Monitoreo_Energetico')
app.register_blueprint(PDFprev_bp, url_prefix='/PDFprev')
app.register_blueprint(scorecard_bp, url_prefix='/Scorecard')
app.register_blueprint(predictores_bp, url_prefix='/Predictores')
app.register_blueprint(analisisE_bp, url_prefix='/AnalisisE')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')

@app.route('/')
def index():
    return render_template('index.html')



