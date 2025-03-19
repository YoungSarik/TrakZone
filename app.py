from flask import Flask, request, send_file
from flask_cors import CORS  
from flask_sqlalchemy import SQLAlchemy
import qrcode
import io
import os  

app = Flask(__name__)
CORS(app)

# Database Configuration (Replace with your credentials)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:admin@5432/trakzone"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)

# Home Route (Fix for Render)
@app.route('/')
def home():
    return "Welcome to the TrakZone QR Code API! Use /generate_qr?data=your_text", 200

# QR Code Generator Route
@app.route('/generate_qr', methods=['GET'])
def generate_qr():
    data = request.args.get('data', 'Default QR Code Data')
    qr = qrcode.make(data)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  
    app.run(host='0.0.0.0', port=port)  # 0.0.0.0 is required for Render
