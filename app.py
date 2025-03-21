from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import qrcode
import io
import os  
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost/trakzone")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "supersecretkey")  
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")  

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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('checkins', lazy=True))
    event = db.relationship('Event', backref=db.backref('checkins', lazy=True))

# 🚀 User Registration
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

# 🔑 User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# 🔒 Protected Example Route
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(message=f"Hello User {current_user}, you have access!"), 200

# 📆 Create an Event
@app.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    data = request.json
    if not all(k in data for k in ("name", "date")):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        event_date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}), 400

    new_event = Event(name=data["name"], date=event_date)
    db.session.add(new_event)
    db.session.commit()
    
    return jsonify({"message": "Event created successfully!", "event_id": new_event.id}), 201

# 📜 List All Events
@app.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    events_list = [{"id": e.id, "name": e.name, "date": e.date.strftime("%Y-%m-%d %H:%M:%S")} for e in events]
    return jsonify(events_list), 200

# 📄 Get Event Details
@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    return jsonify({"id": event.id, "name": event.name, "date": event.date.strftime("%Y-%m-%d %H:%M:%S")}), 200

# 📍 Generate Event QR Code
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

# ✅ Check-in Endpoint
@app.route('/checkin', methods=['POST'])
@jwt_required()
def checkin():
    current_user = int(get_jwt_identity())
    event_id = request.json.get('event_id')

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    existing_checkin = CheckIn.query.filter_by(user_id=current_user, event_id=event_id).first()
    if existing_checkin:
        return jsonify({"message": "You are already checked in!"}), 200

    new_checkin = CheckIn(user_id=current_user, event_id=event_id)
    db.session.add(new_checkin)
    db.session.commit()

    return jsonify({"message": "Check-in successful!"}), 201

# 🎟️ Get Event Attendees
@app.route('/event_attendees/<int:event_id>', methods=['GET'])
def event_attendees(event_id):
    checkins = CheckIn.query.filter_by(event_id=event_id).all()
    attendees = [{"user_id": checkin.user_id, "username": checkin.user.username} for checkin in checkins]
    
    return jsonify({"event_id": event_id, "attendees": attendees})

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  
    app.run(host='0.0.0.0', port=port)
