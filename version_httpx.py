import httpx

# Ruta al archivo PEM que contiene el certificado
path_to_certificate = "/home/samuel/Documents/pkpassApple/pkpassPepephone/certificados/pass.pem"

# Ruta al archivo PEM que contiene la clave privada
path_to_private_key = "/home/samuel/Documents/pkpassApple/pkpassPepephone/certificados/pkpass.pem"

# Contraseña de la clave privada (si la tiene)
passphrase = 'pepe'

# Token de notificación del dispositivo
device_push_token = 'd379c1eb8ed9594be815995751d0ecd105ff3014242e713033ac287ea59910bd'

# Identificador del tema (apns-topic)
pass_type_id = 'pass.com.pepephone.eventTicket'

# URL del servidor de Apple
url = f"https://api.push.apple.com/3/device/{device_push_token}"

# Cabeceras para la solicitud
headers = {
    'apns-topic': pass_type_id,
}

# Datos JSON vacío
data = {}

# Cargar el certificado y la clave privada
cert = (path_to_certificate, path_to_private_key)

# Realizar la solicitud POST
with httpx.Client(cert=cert, verify=True, http2=True) as client:
    response = client.post(url, headers=headers, json=data)

# Obtener la respuesta
status_code = response.status_code
reason_phrase = response.reason_phrase

# Imprimir la respuesta
print("Status Code:", status_code)
print("Reason Phrase:", reason_phrase)
