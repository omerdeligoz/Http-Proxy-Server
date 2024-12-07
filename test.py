import socket

def send_request_via_proxy(proxy_host, proxy_port, request):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((proxy_host, proxy_port))
        client_socket.sendall(request.encode('utf-8'))

        # Receive the response
        response = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response += chunk

        print(response.decode('utf-8'))

# Absolute URL Request
absolute_request = (
    "GET http://localhost:8080/500 HTTP/1.1\r\n"
    "Host: localhost:8080\r\n"
    "\r\n"
)

# Relative URL Request
relative_request = (
    "GET /500 HTTP/1.1\r\n"
    "Host: localhost:8080\r\n"
    "\r\n"
)

# Send through proxy
proxy_host = "localhost"
proxy_port = 8888

print("Sending Absolute URL Request:")
send_request_via_proxy(proxy_host, proxy_port, absolute_request)

print("Sending Relative URL Request:")
send_request_via_proxy(proxy_host, proxy_port, relative_request)
