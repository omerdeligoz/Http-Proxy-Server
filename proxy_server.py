import glob
import socket
import subprocess
import threading
from urllib.parse import urlparse
import os

# Constants
CACHE_DIR = "cache"
WEB_SERVER_HOST = "localhost"
PROXY_PORT = 8888
WEB_SERVER_PORT = 8080
MAX_ALLOWED_SIZE = 9999
MAX_CACHE_SIZE = 0

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


def generate_cache_filename(file_size):
    return os.path.join(CACHE_DIR, str(file_size))


def is_cached(cache_file):
    return os.path.exists(cache_file)


def load_from_cache(cache_file):
    with open(cache_file, "rb") as f:
        return f.read()


def get_cache_size():
    total_size = 0
    for file_path in glob.glob(os.path.join(CACHE_DIR, '*')):
        total_size += os.path.getsize(file_path)
    return total_size


def delete_oldest_cache_files():
    cache_files = glob.glob(os.path.join(CACHE_DIR, '*'))
    cache_files.sort(key=os.path.getmtime)  # Sort by modification time

    while get_cache_size() > MAX_CACHE_SIZE:
        oldest_file = cache_files.pop(0)
        os.remove(oldest_file)
        print(f"Removed oldest cache file: {oldest_file}")


def save_to_cache(cache_file, data):
    # Save the new data to the cache
    with open(cache_file, "wb") as f:
        f.write(data)
    print(f"Saved response to cache: {cache_file}")

    # Check if the cache size exceeds the limit
    if get_cache_size() > MAX_CACHE_SIZE:
        delete_oldest_cache_files()


def send_response(client_socket, client_address, response_code):
    match response_code:
        case 400:
            response_message = (
                "HTTP/1.0 400 Bad Request\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )
        case 404:
            response_message = (
                "HTTP/1.0 404 Not Found\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )
        case 414:
            response_message = (
                "HTTP/1.0 414 Request-URI Too Long\r\n"
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


def forward_request_to_server(client_socket, client_address, hostname, port, request, cache_file):
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

            if cache_file:
                # Save the response to the cache
                save_to_cache(cache_file, response)

            # Send the response back to the client
            client_socket.sendall(response)

    except ConnectionRefusedError:
        send_response(client_socket, client_address, 404)
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

        if parsed_url.scheme and parsed_url.netloc:  # Absolute URI
            host = parsed_url.hostname
            path = parsed_url.path
        else:  # Relative URI
            host = WEB_SERVER_HOST
            path = uri


        # Redirect non-GET requests to the web server
        if method != "GET":
            forward_request_to_server(client_socket, client_address, host, port, request, None)
            return

        # Extract file size from URI
        try:
            file_size = int(path.lstrip("/"))
            if file_size > MAX_ALLOWED_SIZE:
                send_response(client_socket, client_address, 414)
                return
        except Exception:
            forward_request_to_server(client_socket, client_address, host, port, request, None)
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
            forward_request_to_server(client_socket, client_address, host, port, request, cache_file)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()


def start_proxy_server():
    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind(("127.0.0.1", PROXY_PORT))
    proxy_server.listen(5)
    print(f"Proxy server listening on port {PROXY_PORT} with max cache size {MAX_CACHE_SIZE}...")

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
    import sys

    if len(sys.argv) != 2:
        print("Usage: python proxy_server.py <max_cache_size>")
        sys.exit(1)
    MAX_CACHE_SIZE = int(sys.argv[1])
    start_proxy_server()
