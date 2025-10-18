from flask import Blueprint, request, send_file, jsonify, render_template
from flask_cors import CORS
from .PREVENTIVOS_LIB_V1 import procesar_archivos, procesar_archivos_2

PDFprev_bp = Blueprint('PDFprev', __name__, template_folder='../templates', static_folder='../static')
CORS(PDFprev_bp)

@PDFprev_bp.route('/auditorias')
def auditorias():
    return render_template('PDFprev/auditorias.html')

@PDFprev_bp.route('/coordinadores')
def coordinadores():
    return render_template('PDFprev/coordinadores.html')

@PDFprev_bp.route('/PDFprev')
def PDFprev_principal():
    return render_template('PDFprev/PDFprev.html')

@PDFprev_bp.route('/procesar_archivos', methods=['POST'])
def procesar_archivos_route():
    if 'pdf' not in request.files or 'csv' not in request.files:
        return jsonify({"error": "Faltan archivos PDF o CSV"}), 400

    archivo_pdf = request.files['pdf']
    archivo_csv = request.files['csv']
    is_auditorias = request.form.get('isAuditorias') == 'true'

    try:
        if is_auditorias:
            pdf_result = procesar_archivos(archivo_pdf, archivo_csv)
        else:
            pdf_result = procesar_archivos_2(archivo_pdf, archivo_csv)
        download_name = 'Documento_auditorias.pdf' if is_auditorias else 'Documento_coordinadores.pdf'
        return send_file(
            pdf_result,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": f"Error procesando los archivos: {str(e)}"}), 500