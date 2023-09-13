import json
import ssl
import socket
import binascii
import os
from io import BytesIO
from OpenSSL import crypto
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from flask import Flask, Response,request, jsonify, render_template, make_response, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
import subprocess
from config import DATABASE_URI
from db_model import db,Registrations, Apilog, Devices, Passes, Authentication, Clientes, Campaign_rules,Campaign_notifications,Campaigns


app = Flask(__name__)
#user=os.environ['DB_USERNAME'],
#password=os.environ['DB_PASSWORD'])
app.config['SECRET_KEY'] = 'thisissecret'
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
#app.config["SQLALCHEMY_ECHO"] = True
# app.config["SQLALCHEMY_RECORD_QUERIES"] = True
db.init_app(app)


path_pass_generator = "/home/samuel/pass_generator/"

path_to_certificate_p12_convertido = path_pass_generator + "certificados/certificado_completo.pem"
path_to_certificate_p12_crudo = path_pass_generator + "certificados/pkpass.p12"
path_to_certificate = path_pass_generator + "certificados/passcertificate2.pem"
path_to_private_key = path_pass_generator + "certificados/passkey2.pem"
path_certificado_completo = path_pass_generator + "certificado_completo.pem"
path_certificado_apple = path_pass_generator + "certificados/AppleWWDRCA.pem"
#path_to_certificate="/home/samuel/Documents/pkpassApple/pkpassPepephone/certificados/pass.pem"
#path_to_private_key="/home/samuel/Documents/pkpassApple/pkpassPepephone/certificados/pkpass.pem"

app_directory = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta absoluta al directorio "pass_generator"
pass_generator_directory = os.path.join(app_directory, "..", "pass_generator")
# Ruta completa al script auto_new_pass_generator.py
path_auto_new_pass_generator = os.path.join(pass_generator_directory, "auto_new_pass_generator.py")
path_auto_new_pass_regenerator=os.path.join(pass_generator_directory, "auto_pass_regenerator.py")
path_auto_new_pass_fields_regenerator=os.path.join(pass_generator_directory, "auto_new_pass_fields_regenerator.py")


def new_request_print():
    print("\n-----------------------------------------")

def end_request_print():
    print("\n-----------------------------------------\n")

def check_authorization(request):
    cabeceras=request.headers
    authenticationToken = None

    print("Register/unregister request in process.")
    for clave, valor in cabeceras.items():
        if clave=="Authorization":
            partes = valor.split()  # Divide la cadena en partes utilizando el espacio en blanco como separador
            authenticationToken = partes[1] if len(partes) > 1 else None #la 2a parte es el authenticationToken

    if authenticationToken:
        filas = Authentication.query.filter_by(authenticationtoken=authenticationToken).all()
        if filas:
            print("\nAuthentication succeed.")
            return True
    print("\nAuthentication failed.")
    return Response(status=401, mimetype='application/json')

def get_timestamp_actual():
    # Obtener el timestamp actual
    timestamp_actual = datetime.now()
    # Formatear el timestamp como cadena de texto en el formato 'YYYY-MM-DD HH:MM:SS'
    #timestamp_actual.strftime('%d-%m-%Y %H:%M:%S') --> formato no permitido en postgress db
    return timestamp_actual.strftime('%Y-%m-%d %H:%M:%S')

"""----------------------------------ENDPOINTS----------------------------------------------"""
@app.route('/')
def index():
    #return render_template('home.html')
    return render_template('formulario.html')

@app.route('/nuevo_cliente', methods=['POST'])
def nuevo_cliente():
    nombre = request.form['nombre']
    edad = int(request.form['edad'])  # Convertir la edad a entero
    correo = request.form['correo']
    fecha_fin_contrato = datetime.strptime(request.form['fecha_fin_contrato'], '%Y-%m-%d')
    fecha_inicio_contrato = datetime.strptime(request.form['fecha_inicio_contrato'], '%Y-%m-%d')
    genero = request.form['genero']
    
    #Llamamos al script que generará el pase
    result = subprocess.run(['python3', path_auto_new_pass_generator, nombre])

    # Si es 0 el proceso se completó con exito, se creo el nuevo pase del cliente 
    if result.returncode == 0:
        print("\nCreado el nuevo pase del cliente.")
        ruta_directorio_pass=path_pass_generator+f"directorios_punto_pass/{nombre}.pass"
    else:
        print("\n\nError al crear el pase!\n")
        ruta_directorio_pass=""
        # Creamos un objeto Cliente
    nuevo_cliente = Clientes(nombre=nombre, edad=edad, correo=correo, fecha_fin_contrato=fecha_fin_contrato,
                            genero=genero, fecha_inicio_contrato=fecha_inicio_contrato, ruta_directorio_pass=ruta_directorio_pass)

    campaign_ids_cumplidas = segmentar_campañas(nuevo_cliente)
    campaign_id_cumplida = int(campaign_ids_cumplidas[0])
    nuevo_cliente.campaign_id = int(campaign_id_cumplida)
    
    #Almacenamos objeto cliente en la base de datos
    db.session.add(nuevo_cliente)
    db.session.commit()

    return render_template('datos_almacenados.html')

"""----------------------------------ENDPOINTS de CAMPAÑAS----------------------------------------"""
# Ruta para mostrar las campañas y seleccionar una para modificar
@app.route('/mostrar_campaña', methods=['GET', 'POST'])
def mostrar_campaña():
    if request.method == 'POST':
        # Obtener el ID de la campaña seleccionada desde el formulario
        campaign_id = request.form['campaign_id']
        # Redirigir a la página de selección de datos a modificar
        return redirect(f'/modificar_campaña/{campaign_id}')

    # Obtener todas las campañas de la tabla Campaigns
    campañas = Campaigns.query.all()
    return render_template('mostrar_campañas.html', campañas=campañas)

# Ruta para mostrar el menú de selección de datos a modificar
@app.route('/modificar_campaña/<int:campaign_id>', methods=['GET', 'POST'])
def modificar_campaña(campaign_id):
    campaign = Campaigns.query.get(campaign_id)
    if request.method == 'POST':
        # Obtener la opción seleccionada desde el formulario
        opcion = request.form['opcion']

        # Redirigir a la página de edición según la opción seleccionada
        if opcion == '1':
            return redirect(f'/modificar_campaign_dates/{campaign_id}')
        elif opcion == '2':
            return redirect(f'/modificar_campaign_rules/{campaign_id}')
        elif opcion == '3':
            return redirect(f'/modificar_campaign_message/{campaign_id}')
        else:
            # Manejar error si la opción seleccionada no es válida
            return "Opción inválida. Por favor, selecciona una opción válida para modificar."

    return render_template('modificar_campaña.html', campaign=campaign)

@app.route('/modificar_campaign_dates/<int:campaign_id>', methods=['GET', 'POST'])
def modificar_campaign_dates(campaign_id):
    campaign = Campaigns.query.get(campaign_id)
    if request.method == 'POST':
        # Obtener las fechas ingresadas en el formulario
        begin_date = request.form['begin_date']
        end_date = request.form['end_date']

        # Actualizar las fechas en la base de datos
        campaign.begin_date = begin_date
        campaign.end_date = end_date
        db.session.commit()

        # Redirigir a la página de mostrar campañas
        return redirect('/mostrar_campaña')

    return render_template('modificar_campaign_dates.html', campaign=campaign)

@app.route('/modificar_campaign_rules/<int:campaign_id>', methods=['GET', 'POST'])
def modificar_campaign_rules(campaign_id):
    campaign = Campaigns.query.get(campaign_id)
    if request.method == 'POST':
        # Obtener los datos ingresados en el formulario
        age_start = int(request.form['age_start'])
        age_end = int(request.form['age_end'])
        gender = request.form['gender']
        begin_date = datetime.strptime(request.form['begin_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        
        # Buscar el objeto campaign_rules por campaign_id
        campaign_rules = Campaign_rules.query.filter_by(campaign_id=campaign_id).first()

        if campaign_rules is None:
            # Si no existe, crear un nuevo objeto Campaign_rules
            campaign_rules = Campaign_rules(campaign_id=campaign_id, age_start=age_start, age_end=age_end,
                                            gender=gender, begin_date=begin_date, end_date=end_date)
            db.session.add(campaign_rules)
        else:
            # Si ya existe, actualizar sus campos
            campaign_rules.age_start = age_start
            campaign_rules.age_end = age_end
            campaign_rules.gender = gender
            campaign_rules.begin_date = begin_date
            campaign_rules.end_date = end_date

        # Intentar guardar los cambios en la base de datos
        db.session.commit()
        # Redirigir a la página de mostrar campañas
        return redirect('/mostrar_campaña')
    
    return render_template('modificar_campaign_rules.html', campaign=campaign)

@app.route('/modificar_campaign_message/<int:campaign_id>', methods=['GET', 'POST'])
def modificar_campaign_message(campaign_id):
    campaign = Campaigns.query.get(campaign_id)
    if request.method == 'POST':
        # Obtener el mensaje ingresado en el formulario
        message = request.form['message']

        # Actualizar el campo de mensaje en la base de datos
        campaign_notifications = Campaign_notifications.query.filter_by(campaign_id=campaign_id).first()
        if campaign_notifications is not None:
            campaign_notifications.message = message
            db.session.commit()
        else:
            # Mostrar un mensaje de error al usuario
            flash('No se encontró el registro en la tabla campaign_notifications para este campaign_id.', 'error')

        clientes_afectados = Clientes.query.filter_by(campaign_id=campaign_id).all()
        for cliente in clientes_afectados:
            #Llamamos al script que actualiza el pase
            result = subprocess.run(['python3', path_auto_new_pass_regenerator, message, cliente.nombre, str(cliente.campaign_id)])

            # Si es 0 el proceso se completó con exito, se creo el nuevo pase del cliente 
            if result.returncode == 0:
                print("\nPase actualizado con exito, REFRESQUE EL PASE!!!\n")
            else:
                print("\nError al actualizar el pase!\n")

        # Redirigir a la página de mostrar campañas
        return redirect('/mostrar_campaña')

    return render_template('modificar_campaign_message.html', campaign=campaign)

@app.route('/mostrar_clientes')
def mostrar_clientes():
    # Obtener todos los datos de la tabla Clientes
    clientes = Clientes.query.all()
    return render_template('mostrar_clientes.html', clientes=clientes)

@app.route('/modificar_pase/<int:cliente_id>', methods=['GET', 'POST'])
def modificar_pase(cliente_id):
    cliente = Clientes.query.get(cliente_id)
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        ruta_al_pase= cliente.ruta_directorio_pass
        gigas = request.form['gigas']
        facturacion = request.form['facturacion']
        mes = request.form['mes']

        #Llamamos al script que actualiza el pase
        result = subprocess.run(['python3', path_auto_new_pass_fields_regenerator, cliente.nombre, str(cliente.campaign_id),gigas, facturacion, mes, ruta_al_pase])

        # Si es 0 el proceso se completó con exito, se creo el nuevo pase del cliente 
        if result.returncode == 0:
            print("\nPase actualizado con exito, REFRESQUE EL PASE!!!\n")
        else:
            print("\nError al actualizar el pase!\n")

        # Redirigir a la página de mostrar campañas
        return redirect('/mostrar_clientes')
    
    return render_template('modifcar_pase_del_cliente.html',cliente=cliente)

@app.route('/nueva_campaña', methods=['GET', 'POST'])
def nueva_campaña():
    if request.method == 'POST':
        # Obtener los datos del formulario para la nueva campaña
        campaign_title = request.form['campaign_title']
        begin_date = request.form['begin_date']
        end_date = request.form['end_date']

        # Crear una nueva instancia de Campaigns con los datos ingresados
        nueva_campaña = Campaigns(campaign_title=campaign_title, begin_date=begin_date, end_date=end_date)

        # Agregar la nueva campaña a la base de datos
        db.session.add(nueva_campaña)
        db.session.commit()

        # Redirigir a la página para introducir los datos de las nuevas reglas
        return redirect(f'/nuevas_reglas_campaña/{nueva_campaña.campaign_id}')

    return render_template('nueva_campaña.html')

@app.route('/eliminar_campaña/<int:campaign_id>', methods=['POST'])
def eliminar_campaña(campaign_id):
    # Obtener la campaña a eliminar desde la base de datos
    campaign = Campaigns.query.get(campaign_id)
    
    if campaign:
        # Eliminar la campaña de la base de datos
        db.session.delete(campaign)
        db.session.commit()
        
        # Redirigir a la página de mostrar campañas después de la eliminación
        return redirect('/mostrar_campaña')
    else:
        # Manejar error si la campaña no existe
        return "La campaña no existe o ya ha sido eliminada."

@app.route('/nuevas_reglas_campaña/<int:campaign_id>', methods=['GET', 'POST'])
def nuevas_reglas_campaña(campaign_id):
    campaign = Campaigns.query.get(campaign_id)
    if request.method == 'POST':
        # Obtener los datos ingresados en el formulario
        age_start = request.form['age_start']
        age_end = request.form['age_end']
        gender = request.form['gender']
        begin_date = request.form['begin_date']
        end_date = request.form['end_date']

        # Crear una nueva instancia de Campaign_rules con los datos ingresados
        nuevas_reglas = Campaign_rules(campaign_id=campaign_id, age_start=age_start, age_end=age_end,
                                       gender=gender, begin_date=begin_date, end_date=end_date)

        # Agregar las nuevas reglas a la base de datos
        db.session.add(nuevas_reglas)
        db.session.commit()

        # Redirigir a la página de mostrar campañas
        return redirect('/mostrar_campaña')

    return render_template('nuevas_reglas_campaña.html', campaign=campaign)

# ... (otras rutas y configuraciones de la aplicación)

@app.route('/nueva_notificacion_de_campaña/<int:campaign_id>', methods=['GET', 'POST'])
def nueva_notificacion_de_campaña(campaign_id):
    campaign = Campaigns.query.get(campaign_id)
    if request.method == 'POST':
        # Obtener los datos ingresados en el formulario
        message = request.form['message']
        pass_field_to_update = request.form['pass_field_to_update']

        # Crear una nueva instancia de Campaign_notifications con los datos ingresados
        nueva_notificacion = Campaign_notifications(campaign_id=campaign_id, message=message, pass_field_to_update=pass_field_to_update)

        # Agregar la nueva notificación a la base de datos
        db.session.add(nueva_notificacion)
        db.session.commit()

        # Redirigir a la página de mostrar campañas
        return redirect(url_for('mostrar_campaña'))

    return render_template('nuevar_notificacion_campaña.html', campaign=campaign, campaign_id=campaign_id)



"""-------------------------------FUNCIONES AUX----------------------"""
# Función para realizar la segmentación de campañas
def segmentar_campañas(cliente):
    campaign_rules = Campaign_rules.query.filter(
        Campaign_rules.begin_date <= cliente.fecha_inicio_contrato,
        Campaign_rules.end_date >= cliente.fecha_inicio_contrato,
        Campaign_rules.age_start <= cliente.edad,
        Campaign_rules.age_end >= cliente.edad,
    ).all()

    campaign_ids = [rule.campaign_id for rule in campaign_rules]
    return campaign_ids

def obtener_clientes_subscritos(campaign_id):
    # Obtener clientes subscritos a la campaña
    clientes_subscritos = Clientes.query.filter_by(campaign_id=campaign_id).all()

    # Procesar los datos de los clientes
    for cliente in clientes_subscritos:
        ruta_directorio_pass = cliente.ruta_directorio_pass
        # Obtener el campo message de la tabla campaign_notifications
        campaign_notifications = Campaign_notifications.query.filter_by(campaign_id=campaign_id).first()
        message = campaign_notifications.message

        # Llamar a la función que procesa los datos del cliente
        procesar_cliente(cliente, ruta_directorio_pass, message)

def procesar_cliente(cliente, ruta_directorio_pass, message):
    # Implementar la lógica para procesar los datos del cliente y la ruta del directorio pass
    # ...
    return

"""---------------------------------------------ENDPOINTS para tablas de campañas---------------------------------------------"""
# Ruta para el formulario de selección de tabla
@app.route('/insertar_datos_campañas', methods=['GET', 'POST'])
def seleccionar_tabla():
    if request.method == 'POST':
        tabla_seleccionada = request.form['tabla_seleccionada']
        if tabla_seleccionada == 'campaigns':
            return redirect('/insertar_campaigns')
        elif tabla_seleccionada == 'campaign_notifications':
            return redirect('/insertar_campaign_notifications')
        elif tabla_seleccionada == 'campaign_rules':
            return redirect('/insertar_campaign_rules')
    return render_template('seleccionar_tabla_campañas.html')

## Ruta para el formulario de campaigns
@app.route('/insertar_campaigns', methods=['GET', 'POST'])
def insertar_campaigns():
    if request.method == 'POST':
        # Procesar los datos del formulario y guardarlos en la base de datos
        campaign_title = request.form['campaign_title']
        begin_date = datetime.strptime(request.form['begin_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        status = True if request.form['status'] == 'True' else False

        # Crear un nuevo objeto Campaigns y guardarlo en la base de datos
        nueva_campaign = Campaigns(campaign_title=campaign_title, begin_date=begin_date, end_date=end_date, status=status)
        db.session.add(nueva_campaign)
        db.session.commit()

        # Redirigir a una página de éxito o mostrar un mensaje de éxito
        return "Datos de Campaigns almacenados correctamente"

    return render_template('crear_nueva_campaña.html')

# Ruta para el formulario de campaign_notifications
@app.route('/insertar_campaign_notifications', methods=['GET', 'POST'])
def insertar_campaign_notifications():
    if request.method == 'POST':
        # Procesar los datos del formulario y guardarlos en la base de datos
        campaign_id = int(request.form['campaign_id'])
        message = request.form['message']
        pass_field_to_update = request.form['pass_field_to_update']

        # Crear un nuevo objeto Campaign_notifications y guardarlo en la base de datos
        nueva_notificacion = Campaign_notifications(campaign_id=campaign_id, message=message, pass_field_to_update=pass_field_to_update)
        db.session.add(nueva_notificacion)
        db.session.commit()

        # Redirigir a una página de éxito o mostrar un mensaje de éxito
        return "Datos de Campaign_notifications almacenados correctamente"

    # Obtener todas las campañas para mostrarlas en el formulario
    campañas = Campaigns.query.all()
    return render_template('formulario_insertar_campaign_notifications.html', campañas=campañas)

# Ruta para el formulario de campaign_rules
@app.route('/insertar_campaign_rules', methods=['GET', 'POST'])
def insertar_campaign_rules():
    if request.method == 'POST':
        # Procesar los datos del formulario y guardarlos en la base de datos
        campaign_id = int(request.form['campaign_id'])
        age_start = int(request.form['age_start'])
        age_end = int(request.form['age_end'])
        gender = request.form['gender']
        begin_date = datetime.strptime(request.form['begin_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')

        # Crear un nuevo objeto Campaign_rules y guardarlo en la base de datos
        nueva_regla = Campaign_rules(campaign_id=campaign_id, age_start=age_start, age_end=age_end, gender=gender, beginDate=begin_date, endDate=end_date)
        db.session.add(nueva_regla)
        db.session.commit()

        # Redirigir a una página de éxito o mostrar un mensaje de éxito
        return "Datos de Campaign_rules almacenados correctamente"

    # Obtener todas las campañas para mostrarlas en el formulario
    campañas = Campaigns.query.all()
    return render_template('formulario_insertar_campaign_rules.html', campañas=campañas)


"""----------------------------------------------------ENDPOINTS APPLE-----------------------------------------------------------"""

"""Endpoint for registering or unregister a device from server"""
# POST/DELETE request ---> webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier/serialNumber
@app.route('/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/<serialNumber>', methods=['POST','DELETE'])
def register_device(deviceLibraryIdentifier, passTypeIdentifier, serialNumber):

    new_request_print()

    check_authorization(request)
        
    # else:
    #     print("\nAuthentication failed.")
    #     return Response(status=401, mimetype='application/json')
    
    #Payload= body --> push token para mandar notificaciones al pase
    if request.method == 'POST':
        payload = request.json
        #payload=json.loads(payload)
        pushTokenValue=payload.get('pushToken')

        """CHECH IF DEVICE IS ALREADY REGISTREDED"""
        filas = Registrations.query.filter_by(devicelibraryidentifier=deviceLibraryIdentifier,serialnumber=serialNumber,passtypeidentifier=passTypeIdentifier).all()
        if filas:
            print("The pass is already register for this device.")
            end_request_print()
            return Response(status=200, mimetype='application/json')
        else:
            print("Pass not register for this device, registration in process...")

        """Device is not registered --> REGISTRAMOS LOS VALORES EN LA BASE DE DATOS"""    

        #timestamp_formateado = get_timestamp_actual()

        """Obtenemos el timestamp del pase de la tabla pases, para comparar su valor al modificar el pase"""
        updatetimestamp_value = None
        try:
            passes_record = Passes.query.filter_by(serialnumber=serialNumber, passtypeidentifier=passTypeIdentifier).one()
            # Obtenemos el valor del timestamp filtrando por serialNumber y passTypeIdentifier
            updatetimestamp_value = passes_record.updatetimestamp
        except NoResultFound:
            print("\nNo se encontró el registro en la base de datos, se asignara timestamp actual\n.")
            updatetimestamp_value = get_timestamp_actual()

        #Registramos el timestamp de creacion del en la tabla Registrations y Devices
        new_device = Registrations(devicelibraryidentifier=deviceLibraryIdentifier,passtypeidentifier=passTypeIdentifier,serialnumber=serialNumber, updatetimestamp=updatetimestamp_value)
        db.session.add(new_device)
        db.session.commit()
        new_device = Devices(devicelibraryidentifier=deviceLibraryIdentifier,pushtoken=pushTokenValue,updatetimestamp=updatetimestamp_value)
        db.session.add(new_device)
        db.session.commit()
        print("Pass successfully registered.")
        end_request_print()
        return Response(status=201, mimetype='application/json')

    elif request.method == 'DELETE':
        #Eliminamos el pase de las tablas de registro para los servidores de Apple
        filas_register = Registrations.query.filter_by(devicelibraryidentifier=deviceLibraryIdentifier, passtypeidentifier=passTypeIdentifier,serialnumber=serialNumber).all()
        filas_devices = Devices.query.filter_by(devicelibraryidentifier=deviceLibraryIdentifier).all()
        if filas_devices and filas_register:
            try:
                for fila in filas_register:
                    db.session.delete(fila)
                for fila in filas_devices:
                    db.session.delete(fila)
                db.session.commit()
                print("Data successfully deleted.\n")
                print("Pass successfully unregistered.")
            except Exception as exception:
                db.session.rollback()  # Revierte la transacción en caso de error
                print("Error:", str(exception))
        else:
            print("No data to delete.\n")

        #Eliminamos los registros del cliente y de su pase de las tablas de gestion clientes y pases
        try:
            #Obtenemos la ruta al pkpass actualizado para el passID y serialNumber recibidos 
            pass_to_delete = Passes.query.filter_by(serialnumber=serialNumber, passtypeidentifier=passTypeIdentifier).one()
            if not pass_to_delete:
                raise FileNotFoundError("El archivo no existe.")
            nombre_cliente = os.path.splitext(pass_to_delete.pkpass_name)[0]
            cliente_to_delete = Clientes.query.filter_by(nombre=nombre_cliente).one()
            try:
                db.session.delete(pass_to_delete)
                db.session.delete(cliente_to_delete)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()  # Revierte la transacción en caso de error
                print("Error:", str(exception))
        except ValueError as e:
            print(f"Error: no se encontró el dato en la base de datos. \nDetalles del error: {e}")

        end_request_print()
        return Response(status=200, mimetype='application/json')

"""Endpoint for registering logs from apple wallets"""
@app.route('/v1/log', methods=['POST'])
def log():
    payload = request.json['logs']
    log_str = "; ".join(payload)
    print(log_str)
    timestamp=get_timestamp_actual()
    new_log = Apilog(apilog=log_str,timestamp=timestamp)
    db.session.add(new_log)
    db.session.commit()
    return Response(status=200, mimetype='application/json')

"""Endpoint to get the serial numbers of the passes updated"""
# GET request ---> webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier
@app.route('/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>', methods=['GET'])
def get_serial_number_updated(deviceLibraryIdentifier, passTypeIdentifier):
    cabeceras=request.headers
    print(cabeceras)
    serial_num_list = []
    resultados = Registrations.query.filter(Registrations.devicelibraryidentifier == deviceLibraryIdentifier).with_entities(Registrations.serialnumber).all()
    if resultados:
        print("\nLista de serial_numbers actualizables")
        for result in resultados:
            print(result[0])
            #serial_num_list.append(result)
            #añade a la lista solo el serial number, no toda la tupla y usa la lista directamente en el json
            serial_num_list.append(result[0])
        # serial_numbers_separados_por_comas=', '.join([result[0] for result in resultados])
        # print(serial_numbers_separados_por_comas)
        
        timestamp=get_timestamp_actual()
        last_update_to_serial_num_dict = {
            "lastUpdated": timestamp,
            "serialNumbers": serial_num_list
        }
        json_res = json.dumps(last_update_to_serial_num_dict)
        return app.response_class(response=json_res, status=200, mimetype='application/json')
    else:
        return Response(status=204, mimetype='application/json')

"""Endpoint to get the serial numbers of the passes updated, given a timestamp from device to compare """   
# GET request ---> webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier?passesUpdatedSince=tag
@app.route('/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>?passesUpdatedSince=<previousLastUpdated>', methods=['GET'])
def get_serial_number_with_update(deviceLibraryIdentifier, passTypeIdentifier,previousLastUpdated):

    """En esta request cliente, ha recibido notif PUSH y quiere saber serialNumbers de los pases 
    que han sido actualizados. En la request indica un timestamp con el que comparar
    
    Si el timestamp que manda es menos reciente que el almacenado en bd, le indicamos el timestamp nuevo y
    los serialNumbers de los pases que tienen el timestamp desactualizado. Por eso en el if comparo el
    timestamp sacado de la bd y el de la tag en la request recibida"""

    passes_updated_since = request.args.get('passesUpdatedSince')
    cabeceras=request.headers
    print(cabeceras)
    serial_num_list = []
    pass_type_list=[]
    resultados = Registrations.query.filter(Registrations.devicelibraryidentifier == deviceLibraryIdentifier).with_entities(Registrations.serialnumber,Registrations.passtypeidentifier,Registrations.updatetimestamp).all()
    if resultados:
        print("\nLista de serial_numbers actualizables")
        new_timestamp=get_timestamp_actual()
        for resultado in resultados:
            serialnumber = resultado.serialnumber
            serial_num_list.append(resultado.serialnumber)
            passtypeidentifier = resultado.passtypeidentifier
            pass_type_list.append(resultado.passtypeidentifier)
            updatetimestamp = resultado.updatetimestamp
            #Si el timestamp de la request es mas reciente que el almacenado
            if updatetimestamp > passes_updated_since:
                new_timestamp=updatetimestamp

        last_update_to_serial_num_dict = {
            "serialNumbers": serial_num_list,
            "lastUpdated": new_timestamp
        }

        json_res = json.dumps(last_update_to_serial_num_dict)
        return app.response_class(response=json_res, status=200, mimetype='application/json')
    
    else:
        #204 (No content) --> el dispositivo que solicita serial_numbers modificados, no tiene pases registrados
        return Response(status=204, mimetype='application/json')

"""Endpoint to send the updated pass as response"""
@app.route('/v1//passes/<passTypeIdentifier>/<serialNumber>', methods=['GET'])
def get_pass(passTypeIdentifier, serialNumber):
    try:
        #Obtenemos la ruta al pkpass actualizado para el passID y serialNumber recibidos 
        pass_updated = Passes.query.filter_by(serialnumber=serialNumber, passtypeidentifier=passTypeIdentifier).one()
        if not os.path.exists(pass_updated.pkpass_route):
            raise FileNotFoundError("El archivo no existe.")
    except ValueError as e:
            print(f"Error: no se encontró el dato en la base de datos. \nDetalles del error: {e}")
    #Comprobar si el archivo existe
    if os.path.exists(pass_updated.pkpass_route):
        try:
            # Lee el archivo pkpass y obtiene sus bytes
            with open(pass_updated.pkpass_route, 'rb') as file:
                pkpass_bytes = file.read()
            # Procesar el contenido del archivo pkpass como sea necesario
            # ...
            # Resto del código
        except IOError as e:
            print(f"Error al leer el archivo pkpass: {e}")
    else:
        print(f"El archivo pkpass en la ruta '{pass_updated.pkpass_route}' no existe.")

    #Retornamos el pase actualizado como respuesta
    response = Response(pkpass_bytes, content_type='application/vnd.apple.pkpass')
    #response = make_response(send_file(BytesIO(passBytes), mimetype='application/vnd.apple.pkpass'))
    response.headers['Last-Modified'] = get_timestamp_actual()
    return response

"""Endpoint to send notifications to apple server"""
@app.route('/notify_apple_devices/<pass_type_identifier>/<serial_number>', methods=['POST'])
def notify_apple_devices(pass_type_identifier, serial_number):
    device_push_tokens_list = get_device_push_token_list(pass_type_identifier, serial_number)
    for push_token in device_push_tokens_list:
        send_empty_push_notification(push_token,path_to_certificate,path_to_private_key)

    response_text = "Solicitud recibida en la API, notificacion a servidores APNs transmitida."
    return response_text, 200, {'Content-Type': 'text/plain'}

def get_device_push_token_list(pass_type_identifier, serial_number):

    push_token_list=[]
    resultados = Registrations.query.filter_by(passtypeidentifier=pass_type_identifier, serialnumber=serial_number).all()

    # Obtener todos los devicelibraryidentifier de los resultados
    devicelibraries = [registro.devicelibraryidentifier for registro in resultados]
        # Obtener los pushtokens para cada devicelibraryidentifier y agregarlos a la lista
    for devicelibraryidentifier in devicelibraries:
        push_token = get_pushtoken(devicelibraryidentifier)
        if push_token:
            push_token_list.append(push_token)
    
    return push_token_list

def get_pushtoken(devicelibraryidentifier_dado):
    # Filtrar las filas según el valor de devicelibraryidentifier dado
    resultado = Devices.query.filter_by(devicelibraryidentifier=devicelibraryidentifier_dado).one()
    # Obtener el pushtoken del resultado (si existe)
    pushtoken = resultado.pushtoken if resultado else None

    return pushtoken


def load_x509_certificate(path_to_certificate):
    with open(path_to_certificate, 'rb') as cert_file:
        cert_data = cert_file.read()

    return x509.load_pem_x509_certificate(cert_data, default_backend())

def load_x509_certificate_and_private_key(cert_path, passphrase):
    with open(cert_path, 'rb') as cert_file:
        cert_data = cert_file.read()

    # Cargar el certificado X.509 con contraseña utilizando OpenSSL.crypto
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)

    # Cargar la clave privada con contraseña utilizando OpenSSL.crypto
    with open(path_to_private_key, 'rb') as key_file:
        key_data = key_file.read()
        private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_data, passphrase.encode())

    return cert, private_key

def send_empty_push_notification(push_token,path_to_certificate,path_to_private_key):

    thumbprint = "pepe"
    passphrase="pepe"
    #server = "gateway.push.apple.com" 
    #server = "gateway.push.apple.com" 
    server="gateway.push.apple.com"
    port = 2195     # Producción escucha en puerto 2195

    # Cargar el certificado y la clave privada con la passphrase
    #certificate,private_key = load_pem_with_passphrase(path_to_certificate,path_to_private_key, passphrase)
    # Crear un contexto SSL y establecer el certificado y clave privada

    #cert=load_x509_certificate(path_to_certificate)
    cert, private_key = load_x509_certificate_and_private_key(path_to_certificate, passphrase)


    # Crear un contexto SSL hay dos formas
    #context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    #context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # Agregar el certificado al contexto SSL
    #context.load_verify_locations(cadata=cert.public_bytes(encoding=serialization.Encoding.PEM))
    
    # context.use_certificate(cert)
    # context.use_privatekey(private_key)

    context.load_cert_chain(certfile=path_to_certificate, keyfile=path_to_private_key)
    #passphrase.encode()
    #context.load_cert_chain(certfile=path_certificado_completo, password=passphrase)
    # Agregar el certificado al contexto SSL


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with context.wrap_socket(sock, server_hostname=server) as ssl_sock:
            try:
                ssl_sock.connect((server, port))
                ssl_sock.send(build_push_notification(push_token))
            except ssl.SSLError as e:
                raise ssl.SSLError(str(e))
            except socket.error as e:
                raise socket.error(str(e))
    print("Push notification sent successfully!")

    
def load_pem_with_passphrase(path_to_certificate, path_to_private_key, passphrase):
    with open(path_to_certificate, 'rb') as pem_file:
        certificate_pem_data = pem_file.read()

    with open(path_to_private_key, 'rb') as pem_file:
        private_key_pem_data = pem_file.read()

        # Cargar el certificado
        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, certificate_pem_data)

        # Cargar la clave privada con la passphrase usando cryptography
        #private_key = serialization.load_pem_private_key(private_key_pem_data, password=passphrase.encode(), backend=crypto._backend)

        # Cargar la clave privada con la passphrase usando cryptography
        private_key = serialization.load_pem_private_key(private_key_pem_data, password=passphrase.encode())

    return certificate, private_key

def build_push_notification(push_token):
    command = bytes.fromhex('000032')  # Comando para notificación vacía
    device_token = binascii.unhexlify(push_token)
    payload = b'{"aps":""}'
    payload_length = len(payload).to_bytes(2, byteorder='big')
    return command + device_token + payload_length + payload

# Aquí puedes definir tus métodos auxiliares como get_device_push_token_list() y GetAppleServerCert()


"""Endpoint creado por mi, donde se recibira una solicitud una vez se modifique un pase"""
@app.route('/<passTypeIdentifier>/<serialnumber>/modified', methods=['POST'])
def pkpass_update(passTypeIdentifier,serialnumber):
    try:
        # Obtener los datos enviados en el cuerpo de la solicitud
        datos = request.get_json()

        # Obtener la cadena en cuestión
        datos_ruta_pkpass = datos.get("ruta_al_pkpass")

        # Aquí puedes procesar los datos_ruta_pkpass como desees
        # Por ejemplo, imprimirlos en la consola
        print("\nPKPASS ACTUALIZADO")
        print("Pass ID:", passTypeIdentifier)
        print("Serial Number:",serialnumber)
        print("Ruta al pkpass:", datos_ruta_pkpass)

        # Preparar la respuesta para el cliente
        respuesta = {"mensaje": "Datos recibidos correctamente"}

        return jsonify(respuesta), 200

    except Exception as e:
        # En caso de error, devolver un mensaje de error al cliente
        return jsonify({"error": str(e)}), 400
    
if __name__ == '__main__':
    print("----------------------")
    print(" * Process PID", os.getpid())
    print("----------------------")
    with app.app_context():
        #db.init_app(app)
        db.create_all() # <--- create db object.
        #from db_model import Registrations, Apilog, Devices, Passes, Authentication
        
    app.run(debug=True, host='10.0.0.2', port=5000, ssl_context=('/etc/letsencrypt/live/pepephone.jumpingcrab.com/fullchain.pem','/etc/letsencrypt/live/pepephone.jumpingcrab.com/privkey.pem'))
