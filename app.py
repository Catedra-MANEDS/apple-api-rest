import psycopg2
import json
import ssl
import socket
import binascii
from io import BytesIO
from OpenSSL import crypto
from cryptography.hazmat.primitives import serialization
import os
from flask import Flask, Response,request, jsonify, render_template, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
from config import DATABASE_URI
from db_model import db,Registrations, Apilog, Devices, Passes, Authentication, Cliente


app = Flask(__name__)
#user=os.environ['DB_USERNAME'],
#password=os.environ['DB_PASSWORD'])
app.config['SECRET_KEY'] = 'thisissecret'
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
#app.config["SQLALCHEMY_ECHO"] = True
# app.config["SQLALCHEMY_RECORD_QUERIES"] = True
db.init_app(app)

path_to_certificate="/home/samuel/pass_generator/certificados/pass.pem"
path_to_private_key="/home/samuel/pass_generator/certificados/pkpass.pem"
#path_to_certificate="/home/samuel/Documents/pkpassApple/pkpassPepephone/certificados/pass.pem"
#path_to_private_key="/home/samuel/Documents/pkpassApple/pkpassPepephone/certificados/pkpass.pem"

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

@app.route('/')
def index():
    #return render_template('home.html')
    return render_template('formulario.html')

@app.route('/procesar', methods=['POST'])
def procesar_formulario():
    nombre = request.form['nombre']
    edad = request.form['edad']
    correo = request.form['correo']
    fecha_fin_contrato = request.form['fecha_fin_contrato']

    # Creamos un objeto Usuario y lo almacenamos en la base de datos
    usuario = Cliente(nombre=nombre, edad=edad, correo=correo, fecha_fin_contrato=fecha_fin_contrato)
    db.session.add(usuario)
    db.session.commit()

    return render_template('datos_almacenados.html')

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
        try:
            passes_record = Passes.query.filter_by(serialnumber=serialNumber, passtypeidentifier=passTypeIdentifier).one()
            # Obtenemos el valor del timestamp filtrando por serialNumber y passTypeIdentifier
            updatetimestamp_value = passes_record.updatetimestamp
        except NoResultFound:
            print("No se encontró el registro en la base de datos.")

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
        filas_register = Registrations.query.filter_by(devicelibraryidentifier=deviceLibraryIdentifier, passtypeidentifier=passTypeIdentifier,serialnumber=serialNumber).all()
        # if filas_register:
        #     for fila in filas_register:
        #         #print(fila) --> solo muestra el nº de fila donde se encuentra, pero no los valores como tal
        #         #Eso ya se comprueba en la propia query
        #         #print(fila[0]) NO FUNCIONA 
        #         db.session.delete(fila)
        filas_devices = Devices.query.filter_by(devicelibraryidentifier=deviceLibraryIdentifier).all()
        # if filas_devices:
        #     for fila in filas_devices:
        #         db.session.delete(fila)
        # db.session.commit()
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
@app.route('/version/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>', methods=['GET'])
def get_serial_number_updated(deviceLibraryIdentifier, passTypeIdentifier):
    cabeceras=request.headers
    print(cabeceras)
    serial_num_list = []
    resultados = Registrations.query.filter(Registrations.devicelibraryidentifier == deviceLibraryIdentifier).with_entities(Registrations.serialnumber).all()
    if resultados:
        print("\nLista de serial_numbers actualizables")
        for result in resultados:
            print(result[0])
            serial_num_list.append(result)
        serial_numbers_separados_por_comas=', '.join([result[0] for result in resultados])
        print(serial_numbers_separados_por_comas)
        
        timestamp=get_timestamp_actual()
        last_update_to_serial_num_dict = {
            "serialNumbers": serial_num_list,
            "lastUpdated": timestamp
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

    #Obtenemos la ruta al pkpass actualizado para el passID y serialNumber recibidos 
    pass_updated = Passes.query.filter_by(serialnumber=serialNumber, passtypeidentifier=passTypeIdentifier).one()
    if not os.path.exists(pass_updated.pkpass_route):
        raise FileNotFoundError("El archivo no existe.")

    # Lee el archivo y obtiene sus bytes
    with open(pass_updated.pkpass_route, 'rb') as file:
        pkpass_bytes = file.read()

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
    return Response(status=200, mimetype='application/json')

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

def send_empty_push_notification(push_token,path_to_certificate,path_to_private_key):

    thumbprint = "THUMBPRINT_FOR_PASS_TYPE_ID_CERTIFICATE"
    passphrase="pepe"
    server = "gateway.push.apple.com" 
    port = 2195     # Producción escucha en puerto 2195

    # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # context.load_cert_chain(certfile=path_to_certificate, keyfile=path_to_private_key)
    # Crear un contexto SSL

    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    #     with ssl.wrap_socket(sock, certfile=path_to_certificate, keyfile=path_to_private_key) as ssl_sock:
    #         try:
    #             ssl_sock.connect((server, port))
    #             ssl_sock.send(build_push_notification(push_token))
    #         except ssl.SSLError as e:
    #             raise ssl.SSLError(str(e))
    #         except socket.error as e:
    #             raise socket.error(str(e))
    # return "Push notification sent successfully!"
    
    # Cargar el certificado y la clave privada con la passphrase
    certificate,private_key = load_pem_with_passphrase(path_to_certificate,path_to_private_key, passphrase)
    # Crear un contexto SSL y establecer el certificado y clave privada
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    #context.load_cert_chain(certfile=path_to_certificate, keyfile=path_to_private_key, password=passphrase)
    context.load_cert_chain(certfile=path_to_certificate, keyfile=path_to_private_key)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with context.wrap_socket(sock, server_hostname=server) as ssl_sock:
            try:
                ssl_sock.connect((server, port))
                ssl_sock.send(build_push_notification(push_token))
            except ssl.SSLError as e:
                raise ssl.SSLError(str(e))
            except socket.error as e:
                raise socket.error(str(e))
    return "Push notification sent successfully!"

# def load_pem_with_passphrase(path_to_certificate,path_to_private_key,passphrase):
#     with open(path_to_certificate, 'rb') as pem_file:
#         certificate_pem_data = pem_file.read()
#     with open(path_to_private_key, 'rb') as pem_file:
#         private_key_pem_data = pem_file.read()

#         # Cargamos el certificado con la passphrase
#         certificate = crypto.load_certificate(crypto.FILETYPE_PEM, certificate_pem_data)

#         # Crear un objeto bio para leer la clave privada en memoria
#         private_key_bio = crypto._new_mem_buf(private_key_pem_data)
#         # Cargar la clave privada con la passphrase
#         private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, private_key_bio.read(), passphrase)

#         # # Cargamos la clave privada con la passphrase
#         # private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, private_key_pem_data, passphrase)

#         return certificate, private_key
    
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
