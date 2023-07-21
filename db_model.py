from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()
# Create A Model For Table

class Registrations(db.Model):
    __tablename__ = 'registrations'
    pkid = db.Column(db.Integer, primary_key=True)
    devicelibraryidentifier = db.Column(db.String(100))
    passtypeidentifier = db.Column(db.String(100))
    serialnumber=db.Column(db.String(100))
    updatetimestamp=db.Column(db.TIMESTAMP(timezone=False))

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

class Passes(db.Model):
    __tablename__ = 'passes'
    pkid = db.Column(db.Integer, primary_key=True)
    passtypeidentifier = db.Column(db.String(100))
    serialnumber = db.Column(db.String(100))
    pkpass_name = db.Column(db.String(150))
    pkpass_route = db.Column(db.String(200))
    updatetimestamp=db.Column(db.TIMESTAMP(timezone=False))
    passdatajson=db.Column(db.Text)

    __table_args__ = (
        UniqueConstraint('passtypeidentifier', 'serialnumber', name='unique_passes'),
    )

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

class Devices(db.Model):
    __tablename__ = 'devices'
    pkid = db.Column(db.Integer, primary_key=True)
    devicelibraryidentifier = db.Column(db.String(100))
    pushtoken = db.Column(db.String(100))
    updatetimestamp=db.Column(db.TIMESTAMP(timezone=False))
    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

class Apilog(db.Model):
    __tablename__ = 'apilog'
    pkid = db.Column(db.Integer, primary_key=True)
    apilog = db.Column(db.String(5000))
    timestamp=db.Column(db.TIMESTAMP(timezone=False))
    
    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

class Authentication(db.Model):
    __tablename__ = 'authentication'
    authid = db.Column(db.Integer, primary_key=True)
    authenticationtoken = db.Column(db.String(100))
    pkpass_name= db.Column(db.String(100))

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

# Definimos el modelo para la tabla de la base de datos
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80))
    edad = db.Column(db.Integer)
    correo = db.Column(db.String(120))
    fecha_fin_contrato = db.Column(db.Date)

    def __init__(self, nombre, edad, correo, fecha_fin_contrato):
        self.nombre = nombre
        self.edad = edad
        self.correo = correo
        self.fecha_fin_contrato = fecha_fin_contrato
