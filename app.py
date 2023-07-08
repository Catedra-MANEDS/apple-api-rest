from flask import Flask, Response,request, jsonify, render_template, make_response
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
#user=os.environ['DB_USERNAME'],
#password=os.environ['DB_PASSWORD'])

def connect_to_bd():
    con = psycopg2.connect(
    database="passData",
    user="samuel",
    password="hola",
    host="34.175.112.41",
    port= '5432'
    )
    return con

def check_authorization(con,cursor,request):
    cabeceras=request.headers
    authenticationToken = None

    for clave, valor in cabeceras.items():
        if clave=="Authorization":
            partes = valor.split()  # Divide la cadena en partes utilizando el espacio en blanco como separador
            authenticationToken = partes[1] if len(partes) > 1 else None #la 2a parte es el authenticationToken

    if authenticationToken:
        query_sql = "SELECT authenticationToken FROM authentication"
        cursor.execute(query_sql)
        for row in cursor:
            if authenticationToken in row:
                return True
    cursor.close()
    con.close()
    return False

@app.route('/')
def index():
    return render_template('home.html')

# POST request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier/serialNumber
@app.route('/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/<serialNumber>', methods=['POST','DELETE'])
def register_device(deviceLibraryIdentifier, passTypeIdentifier, serialNumber):
    
    con=connect_to_bd()
    cursor = con.cursor()

    if check_authorization(con,cursor,request):
        print("Authentication succeed.")
    else:
        print("Authentication failed.")
        return Response(status=401, mimetype='application/json')
    
    #Payload= body --> push token para mandar notificaciones al pase
    if request.method == 'POST':
        payload = request.json
        #payload=json.loads(payload)
        pushTokenValue=payload.get('pushToken')



        query_sql = "SELECT * FROM registrations WHERE devicelibraryidentifier = %s AND serialnumber = %s AND passtypeidentifier= %s"
        values=(deviceLibraryIdentifier,serialNumber,passTypeIdentifier)
        cursor.execute(query_sql,values)
        existe = cursor.fetchall()#retorna true si se encuentra el valor en la bd

        if existe:
            print("The pass is already register for this device.")
            return Response(status=200, mimetype='application/json')
        else:
            print("Pass not register for this device, registration in process...")

        """REGISTRAMOS LOS VALORES EN LA BASE DE DATOS"""    
        # Obtener el timestamp actual
        timestamp_actual = datetime.now()
        # Formatear el timestamp como cadena de texto en el formato 'YYYY-MM-DD HH:MM:SS'
        timestamp_formateado = timestamp_actual.strftime('%Y-%m-%d %H:%M:%S')
        insert_sql="INSERT INTO devices(deviceLibraryIdentifier,pushToken,updatetimestamp) VALUES(%s,%s,%s)"
        values=(deviceLibraryIdentifier,pushTokenValue,timestamp_formateado)
        cursor.execute(insert_sql,values)
        con.commit()

        insert_sql="INSERT INTO registrations(deviceLibraryIdentifier,passtypeidentifier,serialnumber,updatetimestamp) VALUES(%s,%s,%s,%s)"
        values=(deviceLibraryIdentifier,passTypeIdentifier,serialNumber,timestamp_formateado)
        cursor.execute(insert_sql,values)
        con.commit()
        cursor.close()
        con.close()

        #return jsonify(message="Device registered successfully")
        #data = {'message': 'Resource created'}
        #PRIMER CAMPO DEL RESPONSE --> jsonify(data)
        return Response(status=201, mimetype='application/json')
        # response_data = {'message': 'Registration Successful'}
        # response = jsonify(response_data)
        # response.status_code = 201
        # response.mimetype = 'application/json'
        # return response

    elif request.method == 'DELETE':
        print("\nConnecting to database...")
        query_sql = "SELECT * FROM registrations WHERE devicelibraryidentifier = %s"
        values=(deviceLibraryIdentifier,)
        cursor.execute(query_sql,values)
        existe = cursor.fetchone() is not None #retorna true si se encuentra el valor en la bd
        if existe:
            try:
                print("Deleting data from the database...")
                consulta_eliminar = "DELETE FROM registrations WHERE devicelibraryidentifier = %s"
                values=(deviceLibraryIdentifier,)
                cursor.execute(consulta_eliminar,values)
                con.commit()
                consulta_eliminar = "DELETE FROM devices WHERE devicelibraryidentifier = %s"
                values=(deviceLibraryIdentifier,)
                cursor.execute(consulta_eliminar,values)
                con.commit()
                cursor.close()
                con.close()
            except Exception as e:
                con.rollback()  # Revierte la transacción en caso de error
                print("Error:", e)

        print("Data successfully deleted.\n")
        return Response(status=200, mimetype='application/json')

@app.route('/v1/log', methods=['POST'])
def log():
    payload = request.json['logs']
    log_str = "; ".join(payload)
    print(log_str)
    
    # Save to ApplePassAPILog SQL table
    return Response(status=200, mimetype='application/json')


# GET request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier
@app.route('/version/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>', methods=['GET'])
def get_serial_number(deviceLibraryIdentifier, passTypeIdentifier):

    con=connect_to_bd()
    cursor = con.cursor()
    if request.method == 'GET':
        #El body a recibir es el push token para mandar notificaciones al pase
        payload = request.json
        print("\n--------------Registration endpoint--------------\n")
        print(payload)
        #payload=json.loads(payload)
        pushTokenValue=payload.get('pushToken')

        print("\n--------------Headers--------------\n")
        print(request.headers)
        cabeceras=request.headers
        for clave, valor in cabeceras.items():
            if clave=="Authorization":
                #print(clave + ": " + valor)
                partes = valor.split()  # Divide la cadena en partes utilizando el espacio en blanco como separador
                authenticationToken = partes[1] #la 2a parte es el authenticationToken


    # TODO: Implementar la lógica de obtención del número de serie
    return jsonify(serialNumber="XXX")

# GET request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier?passesUpdatedSince=tag
@app.route('/version/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>', methods=['GET'])
def get_serial_number_updated(deviceLibraryIdentifier, passTypeIdentifier):
    passes_updated_since = request.args.get('passesUpdatedSince')
    # TODO: Implementar la lógica de obtención del número de serie con la fecha de actualización
    return jsonify(serialNumber="XXX", lastUpdated="YYYY-MM-DD HH:mm:ss")


# POST request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier/serialNumber
@app.route('/version/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/serialNumber', methods=['POST'])
def register_device_original(deviceLibraryIdentifier, passTypeIdentifier, serialNumber):
    payload = request.json
    # TODO: Implementar la lógica de registro del dispositivo en la base de datos
    return jsonify(message="Device registered successfully")


# DELETE request to webServiceURL/version/devices/deviceLibraryIdentifier/registrations/passTypeIdentifier/serialNumber
@app.route('/version/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/serialNumber', methods=['DELETE'])
def unregister_device(deviceLibraryIdentifier, passTypeIdentifier, serialNumber):
    # TODO: Implementar la lógica de eliminación del dispositivo de la base de datos
    return jsonify(message="Device unregistered successfully")

if __name__ == '__main__':
    #host='192.168.0.105' --> para cambiar la direc IP donde se levanta la app
    #port='5000'
    #/home/samuel/apiRest/certificate.pem
    #/home/samuel/apiRest/key.pem
    print("----------------------")
    print(" * Process PID", os.getpid())
    print("----------------------")
    app.run(debug=True, ssl_context=('/etc/letsencrypt/live/pepephone.jumpingcrab.com/fullchain.pem','/etc/letsencrypt/live/pepephone.jumpingcrab.com/privkey.pem'),host='10.0.0.2', port=5000)
