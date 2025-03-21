from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import qrcode
import io
import os  
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:admin@localhost/trakzone"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "supersecretkey")
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")  # Change for deployment

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Event Model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

# Check-in Model
class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('checkins', lazy=True))
    event = db.relationship('Event', backref=db.backref('checkins', lazy=True))

# Register Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Missing required fields"}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(username=data['username'], email=data['email'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

# Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)  # Keep ID as integer
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Protected Endpoint (Example)
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(message=f"Hello User {current_user}, you have access!"), 200

# Generate Event QR Code
@app.route('/generate_qr/<int:event_id>', methods=['GET'])
def generate_event_qr(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    qr_data = f"{API_URL}/checkin?event_id={event_id}"
    qr = qrcode.make(qr_data)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

# Check-in Endpoint
@app.route('/checkin', methods=['POST'])
@jwt_required()
def checkin():
    current_user = int(get_jwt_identity())  # Ensure it's an integer
    event_id = request.json.get('event_id')

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Prevent duplicate check-ins
    existing_checkin = CheckIn.query.filter_by(user_id=current_user, event_id=event_id).first()
    if existing_checkin:
        return jsonify({"message": "You are already checked in!"}), 200

    new_checkin = CheckIn(user_id=current_user, event_id=event_id)
    db.session.add(new_checkin)
    db.session.commit()

    return jsonify({"message": "Check-in successful!"}), 201

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  
    app.run(host='0.0.0.0', port=port)
