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
class Clientes(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(80))
    edad = db.Column(db.Integer)
    correo = db.Column(db.String(120))
    fecha_fin_contrato = db.Column(db.Date)
    fecha_inicio_contrato = db.Column(db.Date)
    genero = db.Column(db.String(15))
    ruta_directorio_pass = db.Column(db.String(200))

    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'))
    campaign = db.relationship('Campaigns', backref='clientes')


"""---------------------MODELO DE TABLAS DE CAMPAÑAS DE NOTIFICACIONES------------------"""
# Modelo de la tabla "Campaigns"
class Campaigns(db.Model):
    __tablename__ = 'campaigns'
    campaign_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_title = db.Column(db.String(100), nullable=False)
    begin_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.Boolean)

    campaign_notifications = db.relationship('Campaign_notifications', back_populates='campaign', cascade="all, delete-orphan")
    campaign_rules = db.relationship('Campaign_rules', back_populates='campaign', cascade="all, delete-orphan")
    #campaign_subscriptions = db.relationship('Campaigns_subscriptions', back_populates='campaign')


# Modelo de la tabla "Campaign_notifications"
class Campaign_notifications(db.Model):
    __tablename__ = 'campaign_notifications'
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    pass_field_to_update = db.Column(db.String(150))

    campaign = db.relationship('Campaigns', back_populates='campaign_notifications')

# Modelo de la tabla "Campaign_rules"
class Campaign_rules(db.Model):
    __tablename__ = 'campaign_rules'
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), primary_key=True)
    age_start = db.Column(db.Integer)
    age_end = db.Column(db.Integer)
    gender = db.Column(db.String(15))
    begin_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    campaign = db.relationship('Campaigns', back_populates='campaign_rules')

"""ESTA TABLA NO LA USO"""
# Modelo de la tabla "CampaignsSubscriptions"
# class Campaigns_subscriptions(db.Model):
#     __tablename__ = 'campaigns_subscriptions'
#     campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), primary_key=True)
#     serialnumber = db.Column(db.String(100))
#     passTypeIdentifier = db.Column(db.String(100))
#     pushToken = db.Column(db.String(150))

#     campaign = db.relationship('Campaigns', back_populates='campaign_subscriptions')

