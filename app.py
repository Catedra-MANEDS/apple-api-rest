from flask import Flask, Response,request, jsonify, render_template, make_response, send_file
import psycopg2
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from config import DATABASE_URI
from db_model import db,Registrations, Apilog, Devices, Passes, Authentication
from io import BytesIO


app = Flask(__name__)
#user=os.environ['DB_USERNAME'],
#password=os.environ['DB_PASSWORD'])
app.config['SECRET_KEY'] = 'thisissecret'
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
# app.config["SQLALCHEMY_ECHO"] = True
# app.config["SQLALCHEMY_RECORD_QUERIES"] = True
db.init_app(app)

def check_authorization(request):
    cabeceras=request.headers
    authenticationToken = None

    for clave, valor in cabeceras.items():
        if clave=="Authorization":
            partes = valor.split()  # Divide la cadena en partes utilizando el espacio en blanco como separador
            authenticationToken = partes[1] if len(partes) > 1 else None #la 2a parte es el authenticationToken

    if authenticationToken:
        filas = Authentication.query.filter_by(authenticationtoken=authenticationToken).all()
        if filas:
            return True
    return False

def get_timestamp():
    # Obtener el timestamp actual
    timestamp_actual = datetime.now()
    # Formatear el timestamp como cadena de texto en el formato 'YYYY-MM-DD HH:MM:SS'
    return timestamp_actual.strftime('%d-%m-%Y %H:%M:%S')

def new_request_print():
    print("\n-----------------------------------------")

def end_request_print():
    print("\-----------------------------------------\n")

@app.route('/')
def index():
    return render_template('home.html')

# POST/DELETE request to 
#   webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier/serialNumber
@app.route('/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/<serialNumber>', methods=['POST','DELETE'])
def register_device(deviceLibraryIdentifier, passTypeIdentifier, serialNumber):

    new_request_print()
    print("Register/unregister request in process.")
    if check_authorization(request):
        print("\nAuthentication succeed.")
    else:
        print("\nAuthentication failed.")
        return Response(status=401, mimetype='application/json')
    
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

        """REGISTRAMOS LOS VALORES EN LA BASE DE DATOS"""    

        timestamp_formateado = get_timestamp()
        new_device = Registrations(devicelibraryidentifier=deviceLibraryIdentifier,passtypeidentifier=passTypeIdentifier,serialnumber=serialNumber, updatetimestamp=timestamp_formateado)
        db.session.add(new_device)
        db.session.commit()
        new_device = Devices(devicelibraryidentifier=deviceLibraryIdentifier,pushtoken=pushTokenValue,updatetimestamp=timestamp_formateado)
        db.session.add(new_device)
        db.session.commit()
        print("Pass successfully registered.")
        #return jsonify(message="Device registered successfully")
        #data = {'message': 'Resource created'}
        #PRIMER CAMPO DEL RESPONSE --> jsonify(data)
        end_request_print()
        return Response(status=201, mimetype='application/json')
        # response_data = {'message': 'Registration Successful'}
        # response = jsonify(response_data)
        # response.status_code = 201
        # response.mimetype = 'application/json'
        # return response

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
        if filas_devices or filas_register:
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

@app.route('/v1/log', methods=['POST'])
def log():
    payload = request.json['logs']
    log_str = "; ".join(payload)
    print(log_str)
    timestamp=get_timestamp()
    new_log = Apilog(apilog=log_str,timestamp=timestamp)
    db.session.add(new_log)
    db.session.commit()
    return Response(status=200, mimetype='application/json')


# GET request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier
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
        
        timestamp=get_timestamp()
        last_update_to_serial_num_dict = {
            "serialNumbers": serial_num_list,
            "lastUpdated": timestamp
        }
        json_res = json.dumps(last_update_to_serial_num_dict)
        return app.response_class(response=json_res, status=200, mimetype='application/json')
    else:
        return Response(status=204, mimetype='application/json')
    
# GET request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier?passesUpdatedSince=tag
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
        new_timestamp=get_timestamp()
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
    #204 (No content) --> el dispositivo que solicita serial_numbers modificados, no tiene pases registrados
    else:
        return Response(status=204, mimetype='application/json')

#Este es el endpoint para mandar el nuevo pase como respuesta
"""Wallet request to get the updated pass, giving:
    -passTypeIdentifier
    -serialNumber"""
@app.route('/v1//passes/<passTypeIdentifier>/<serialNumber>', methods=['GET'])
def get_pass(passTypeIdentifier, serialNumber):
    # Si hubo nuevas actualizaciones, vuelve a generar todo el Pass.
    passBytes = generate_pass(passTypeIdentifier, serialNumber)
    
    # Crear una respuesta HTTP
    response = make_response(send_file(BytesIO(passBytes), mimetype='application/vnd.apple.pkpass'))
    response.headers['Last-Modified'] = get_timestamp()
    return response

def generate_pass(passTypeIdentifier, serialNumber):
    
    try:
        # Envía el archivo como respuesta
        return send_file(ruta_archivo, as_attachment=True)
    except Exception as e:
        # Maneja el caso de error, por ejemplo, si el archivo no existe
        return str(e), 404
    passBytes = b'This is a sample Pass'
    return passBytes

if __name__ == '__main__':
    print("----------------------")
    print(" * Process PID", os.getpid())
    print("----------------------")
    with app.app_context():
        #db.init_app(app)
        db.create_all() # <--- create db object.
        #from db_model import Registrations, Apilog, Devices, Passes, Authentication
        
    app.run(debug=True, host='10.0.0.2', port=5000, ssl_context=('/etc/letsencrypt/live/pepephone.jumpingcrab.com/fullchain.pem','/etc/letsencrypt/live/pepephone.jumpingcrab.com/privkey.pem'))
