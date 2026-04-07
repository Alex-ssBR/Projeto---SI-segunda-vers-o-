from . import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Patrimonio(db.Model):
    __tablename__ = 'patrimonios'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    # Cascade aqui apaga os casos se o patrimonio for deletado
    casos = db.relationship('Caso', backref='patrimonio', cascade="all, delete-orphan")

class Caso(db.Model):
    __tablename__ = 'casos'
    id = db.Column(db.Integer, primary_key=True)
    patrimonio_id = db.Column(db.Integer, db.ForeignKey('patrimonios.id'))
    solicitante = db.Column(db.String(100))
    secretaria = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    ramal = db.Column(db.String(20))
    problema = db.Column(db.Text)
    status = db.Column(db.String(20), default='aberto')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    # ADICIONADO: Cascade aqui apaga os tickets se o caso for deletado
    tickets = db.relationship('Ticket', backref='caso', cascade="all, delete-orphan")

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    caso_id = db.Column(db.Integer, db.ForeignKey('casos.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    mensagem = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario')

class Aviso(db.Model):
    __tablename__ = 'avisos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    mensagem = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario')

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    acao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario')