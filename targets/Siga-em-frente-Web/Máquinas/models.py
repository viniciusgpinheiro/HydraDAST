from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'operator' ou 'admin'
    booth_id = db.Column(db.Integer, nullable=True)  # Para operadores, qual cabine trabalha
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    messages = db.relationship('Message', backref='recipient', lazy=True, foreign_keys='Message.recipient_id')
    transfers_sent = db.relationship('Transfer', backref='operator', lazy=True, foreign_keys='Transfer.operator_id')

class Booth(db.Model):
    __tablename__ = 'booths'
    
    id = db.Column(db.Integer, primary_key=True)
    booth_number = db.Column(db.Integer, unique=True, nullable=False)
    total_vehicles = db.Column(db.Integer, default=0)
    total_cash = db.Column(db.Float, default=0.0)
    pix_key = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Vulnerável a XSS armazenado
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', backref='sent_messages', foreign_keys=[sender_id])

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Transfer(db.Model):
    __tablename__ = 'transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_booth = db.Column(db.Integer, db.ForeignKey('booths.id'), nullable=False)
    destination_booth = db.Column(db.Integer, db.ForeignKey('booths.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
