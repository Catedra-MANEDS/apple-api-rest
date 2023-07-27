def send_empty_push_notification(push_token):
    thumbprint = "THUMBPRINT_FOR_PASS_TYPE_ID_CERTIFICATE"
    server = "gateway.push.apple.com"  # Producción
    port = 2195

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="path/to/your/certificate.pem", keyfile="path/to/your/private-key.pem")

    with socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with context.wrap_socket(sock, server_hostname=server) as ssock:
            try:
                ssock.connect((server, port))
            except Exception as e:
                raise Exception("Error al conectar con el servidor de Apple:", e)

            push_token_bytes = binascii.unhexlify(push_token.upper())
            payload = '{"aps":""}'

            notification = b'\x00' + b'\x00' + b'\x20' + push_token_bytes + b'\x00' + len(payload).to_bytes(1, 'big') + payload.encode('utf-8')

            try:
                ssock.sendall(notification)
            except Exception as e:
                raise Exception("Error al enviar la notificación:", e)



