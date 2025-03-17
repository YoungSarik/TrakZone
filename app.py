from flask import Flask, request, send_file
from flask_cors import CORS  # Разрешает запросы с других доменов (CORS)
import qrcode
import io

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех источников

@app.route('/generate_qr', methods=['GET'])
def generate_qr():
    data = request.args.get('data', 'Default QR Code Data')

    # Генерация QR-кода
    qr = qrcode.make(data)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
