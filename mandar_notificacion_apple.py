#!/usr/bin/python3
import requests
import ssl
import httpx
import binascii
import socket


directorio_certificados="/home/samuel/Documents/pkpassApple/pkpassPepephone/scp_mandar/certificados/"

#Certificado del pase
#path_to_certificate=directorio_certificados+"passcertificate2.pem"
path_to_certificate=directorio_certificados+"passcertificate_completo3.pem"

#Clave del pase
path_to_private_key=directorio_certificados+"passkey2.pem"

#Certificado de apple
certificado_apple=directorio_certificados+"AppleWWDRCA.pem"

def build_push_notification(push_token):
    command = bytes.fromhex('000032')  # Comando para notificación vacía
    device_token = binascii.unhexlify(push_token)
    device_token
    payload = b'{"aps":""}'
    payload_length = len(payload).to_bytes(2, byteorder='big')
    return command + device_token + payload_length + payload

# Contraseña de la clave privada (si la tiene)
passphrase = 'pepe'

# Token de notificación del dispositivo
device_push_token = 'd379c1eb8ed9594be815995751d0ecd105ff3014242e713033ac287ea59910bd'

# Identificador del tema (apns-topic)
pass_type_id = 'pass.com.pepephone.eventTicket'

# URL del servidor de Apple
url = f"https://api.push.apple.com/3/device/{device_push_token}"

# # Cargar el certificado y la contraseña
# context = ssl.create_default_context()
# #context.load_cert_chain(certfile=path_to_certificate, password=pem_secret)
# context.load_cert_chain(certfile=path_to_certificate, keyfile=path_to_private_key, password=passphrase)
# # Cabeceras para la solicitud
# headers = {
#     'apns-topic': pass_type_id,
# }

# # Datos JSON vacío
# data = {}

# notification_payload=build_push_notification(device_push_token)

# Establecer el servidor al que te conectarás
server="api.push.apple.com"
port = 2197     # Producción escucha en puerto 2195

# Crear un contexto SSL hay dos formas
#context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

# Agregar el certificado al contexto SSL
#context.load_verify_locations(cadata=cert.public_bytes(encoding=serialization.Encoding.PEM)) 
# context.use_certificate(cert)
# context.use_privatekey(private_key)

context.load_cert_chain(certfile=path_to_certificate)
#passphrase.encode()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    with context.wrap_socket(sock, server_hostname=server) as ssl_sock:
        try:
            ssl_sock.connect((server, port))
            ssl_sock.send(build_push_notification(device_push_token))
        except ssl.SSLError as e:
            raise ssl.SSLError(str(e))
        except socket.error as e:
            raise socket.error(str(e))
print("Push notification sent successfully!")

# # Conectar al servidor
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#     with context.wrap_socket(sock, server_hostname=server) as ssl_sock:
#         try:
#             ssl_sock.connect((server, port))
#             # Aquí puedes continuar con el envío de la notificación push
#         except ssl.SSLError as e:
#             raise ssl.SSLError(str(e))
#         except socket.error as e:
#             raise socket.error(str(e))

# cert = (path_to_certificate, path_to_private_key)
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
# context.load_cert_chain(certfile=path_to_certificate, keyfile=path_to_private_key, password=passphrase)

# # Realizar la solicitud POST
# with httpx.Client(http2=True, headers=headers, verify=False) as client:
#     response = client.post(url, data=notification_payload)

# # Realizar la solicitud POST
# # with httpx.Client(cert=cert, verify=True, http2=True) as client:
# #     response = client.post(url,headers=headers, json=data)

# status_code = response.status_code
# reason_phrase = response.reason_phrase

# # Imprimir la respuesta
# print("Status Code:", status_code)
# print("Reason Phrase:", reason_phrase)

# # Obtener la respuesta
# status_code = response.status_code
# reason_phrase = response.reason

# # Imprimir la respuesta
# print("Status Code:", status_code)
# print("Reason Phrase:", reason_phrase)
