import socket
import threading

# Constants
MIN_SIZE = 100
MAX_SIZE = 20000
VALID_METHODS = {"GET", "HEAD", "POST", "PUT"}


# Generate an HTML document of the given size
def generate_html(size):
    content = "x" * (size - 75 - len(str(size)))  # Adjust size for HTML tags
    return f"<HTML>\n<HEAD>\n<TITLE>I am {size} bytes long</TITLE>\n</HEAD>\n<BODY>{content}</BODY>\n</HTML>"


def send_response(client_socket, client_address, response_code, size=None):
    match response_code:
        case 200:
            html_content = generate_html(size)
            response_message = (
                f"HTTP/1.0 200 OK\r\n"
                f"Content-Type: text/html\r\n"
                f"Content-Length: {len(html_content)}\r\n"
                f"\r\n"
                f"{html_content}"
            )
        case 400:
            response_message = (
                "HTTP/1.0 400 Bad Request\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )
        case 501:
            response_message = (
                "HTTP/1.0 501 Not Implemented\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )

        case _:
            response_message = (
                "HTTP/1.0 500 Internal Server Error\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )
    client_socket.sendall(response_message.encode('utf-8'))
    print(f"Response to {client_address}:\n{response_message}")


def handle_client(client_socket, client_address):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        print(f"Received request:\n{request}")

        if not request:
            return

        request_lines = request.split('\r\n')
        method, uri, version = request_lines[0].split(' ', 2)
        if method not in {"HEAD", "POST", "PUT", "GET"}:
            # If method is invalid, return 400 Bad Request
            send_response(client_socket, client_address, 400)
            return

        if method in {"HEAD", "POST", "PUT"}:
            # If method is HEAD, POST, or PUT, return 501 Not Implemented
            send_response(client_socket, client_address, 501)
            return

        # Parse URI
        if not uri.startswith("/"):
            send_response(client_socket, client_address, 400)
            return

        uri = uri.lstrip("/")

        if not uri.isdigit():
            # If URI is not an integer, return 400 Bad Request
            send_response(client_socket, client_address, 400)
            return

        size = int(uri)
        if size < MIN_SIZE or size > MAX_SIZE:
            # If size is out of range, return 400 Bad Request
            send_response(client_socket, client_address, 400)
            return

        # Generate HTML document
        send_response(client_socket, client_address, 200, size)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()


def start_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", port))
    server.listen(5)
    print(f"Server listening on port {port}")

    while True:
        try:
            client_socket, client_address = server.accept()
            print("-" * 100)
            print(f"Accepted connection from {client_address}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down the server...")
            server.close()
            break


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python http_server.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    start_server(port)
