import socket
import threading
from urllib.parse import urlparse
import os

# Constants
CACHE_DIR = "./cache"
WEB_SERVER_HOST = "localhost"
PROXY_PORT = 8888
WEB_SERVER_PORT = 8080
MAX_ALLOWED_SIZE = 9999

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


def generate_cache_filename(file_size):
    return os.path.join(CACHE_DIR, str(file_size))


def is_cached(cache_file):
    return os.path.exists(cache_file)


def load_from_cache(cache_file):
    with open(cache_file, "rb") as f:
        return f.read()


def save_to_cache(cache_file, data):
    with open(cache_file, "wb") as f:
        f.write(data)


def send_response(client_socket, client_address, response_code):
    match response_code:
        case 400:
            response_message = "HTTP/1.0 400 Bad Request\r\n"
        case 404:
            response_message = "HTTP/1.0 404 Not Found\r\n"
        case 414:
            response_message = "HTTP/1.0 414 Request-URI Too Long\r\n"
        case 501:
            response_message = "HTTP/1.0 501 Not Implemented\r\n"
        case _:
            response_message = "HTTP/1.0 500 Internal Server Error\r\n"

    client_socket.sendall(response_message.encode('utf-8'))
    print(f"Response to {client_address}:\n{response_message}")


def forward_request_to_server(client_socket, hostname, port, request, cache_file):
    try:
        # Connect to the web server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.connect((hostname, port))

            # Parse the request line
            request_lines = request.split('\r\n')
            method, uri, version = request_lines[0].split(' ', 2)

            # Parse the URI
            parsed_url = urlparse(uri)
            relative_path = parsed_url.path

            # Reconstruct the request line with the relative path
            request_lines[0] = f"{method} {relative_path} {version}"
            modified_request = '\r\n'.join(request_lines)

            # Send the modified request to the server
            server_socket.sendall(modified_request.encode('utf-8'))

            # Receive the response from the web server
            response = b""
            while True:
                chunk = server_socket.recv(4096)
                if not chunk:
                    break
                response += chunk

            if cache_file:  # Method is get and file size is within range
                # Save the response to the cache
                save_to_cache(cache_file, response)
                print(f"Saved response to cache: {cache_file}")

            # Send the response back to the client
            client_socket.sendall(response)

    except ConnectionRefusedError:
        send_response(client_socket, 404)
        print("Web server not found.")
    except Exception as e:
        print(f"Error forwarding request to server: {e}")


def handle_proxy_client(client_socket, client_address):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        first_line = request.split('\r\n')[0]
        print(f"Accept from client:\n{first_line}")

        request_lines = request.split('\r\n')
        method, uri, version = request_lines[0].split(' ', 2)

        # Parse URI
        parsed_url = urlparse(uri)
        port = parsed_url.port or 80

        # TODO differentiate between absolute and relative URIs (CONNECT methods are problematic)
        if parsed_url.scheme and parsed_url.netloc:  # Absolute URI
            host = parsed_url.hostname
            path = parsed_url.path
        else:  # Relative URI
            host = WEB_SERVER_HOST
            path = uri

        # TODO Bonus part for directing requests to other servers
        if host != WEB_SERVER_HOST:
            print(f"Redirecting to {host}")
            forward_request_to_server(client_socket, host, port, request, None)
            return

        # Redirect non-GET requests to the web server
        if method != "GET":
            forward_request_to_server(client_socket, host, port, request, None)
            return

        # Extract file size from URI
        try:
            file_size = int(path.lstrip("/"))
            if file_size > MAX_ALLOWED_SIZE:
                send_response(client_socket, client_address, 414)
                return
        except Exception:
            forward_request_to_server(client_socket, host, port, request, None)
            return

        # Generate cache file name
        cache_file = generate_cache_filename(file_size)

        # Check cache
        if is_cached(cache_file):
            print(f"Cache hit: Serving from cache {cache_file}")
            cached_response = load_from_cache(cache_file)
            client_socket.sendall(cached_response)
        else:
            print("Cache miss: Forwarding request to server.")
            forward_request_to_server(client_socket, host, port, request, cache_file)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()


def start_proxy_server(port):
    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind(("", port))
    proxy_server.listen(5)
    print(f"Proxy server listening on port {port}...")

    while True:
        try:
            client_socket, client_address = proxy_server.accept()
            print("-" * 100)
            print(f"Accepted connection from {client_address}")
            client_thread = threading.Thread(target=handle_proxy_client, args=(client_socket, client_address))
            client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down the proxy server...")
            proxy_server.close()
            break


if __name__ == "__main__":
    start_proxy_server(PROXY_PORT)
