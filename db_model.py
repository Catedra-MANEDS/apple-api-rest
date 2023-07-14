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

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()
