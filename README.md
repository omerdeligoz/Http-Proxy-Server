# HTTP Server and Proxy Server

## Overview

This repository contains two Python-based servers:

- **HTTP Server (`http_server.py`)**: A simple HTTP server that dynamically generates HTML documents of a specified size. The server accepts GET requests where the URL path represents the desired size (in bytes) of the HTML document (e.g., `/150` returns a 150-byte HTML page). It performs error checking and returns appropriate HTTP status codes (such as 400 for bad requests and 501 for unsupported methods).

- **Proxy Server (`proxy_server.py`)**: A lightweight proxy server that forwards client requests to a web server and caches the responses locally. The proxy handles GET requests specially by caching responses (using a cache directory) based on the requested size. For non-GET requests or requests not meeting the caching criteria, it simply forwards the request to the target server. The cache size is managed automatically by deleting the oldest cached files when the total exceeds a specified limit.

## Features

- **Dynamic HTML Generation**: Generate HTML documents of a specific byte size on the fly.
- **Error Handling**: Return HTTP error codes (400, 414, 501, etc.) for malformed or unsupported requests.
- **Caching Mechanism**: Improve response times by caching server responses and serving them for repeated requests.
- **Concurrency**: Use of a thread pool (`ThreadPoolExecutor`) to handle multiple client connections concurrently.

## Prerequisites

- Python 3.x
- No external libraries are required as both scripts use only Python's standard library.

## Getting Started

### Running the HTTP Server

1. Open a terminal and navigate to the repository directory.
2. Start the HTTP server by specifying a port (e.g., 8080):
   ```bash
   python http_server.py 8080
3. Test the server by opening a web browser or using `curl`:
   - Example: [http://localhost:8080/150](http://localhost:8080/150) will generate a 150-byte HTML document.

### Running the Proxy Server

1. Open another terminal and navigate to the repository directory.
2. Start the proxy server by specifying the maximum cache size (in bytes). For example, to set a maximum cache size of 100,000 bytes:
   ```bash
   python proxy_server.py 100000
3. To test the proxy, configure your browser to use `localhost:8888` as the proxy or use `curl` with proxy settings:
   ```bash
   curl -x localhost:8888 http://localhost:8080/150

## Directory Structure

```
.
├── http_server.py        # HTTP server that generates HTML documents based on a requested size.
├── proxy_server.py       # Proxy server with caching functionality.
└── cache/                # Directory used for caching responses (created automatically).
```

## How It Works

- **HTTP Server**:
  - Receives a GET request with a numerical path (representing the desired HTML size).
  - Validates the requested size against defined limits.
  - Generates an HTML document of the specified size.
  - Returns error responses for invalid requests (e.g., if the size is out of range or if the request method is not GET).

- **Proxy Server**:
  - Receives client requests and determines if the request should be served from cache.
  - For GET requests with a numerical path, it checks if a cached version exists.
  - If a cached version is found, it serves that directly; otherwise, it forwards the request to the HTTP server, caches the response, and then serves it.
  - Non-GET requests are forwarded directly to the web server without caching.

## Contributing

Contributions are welcome! Feel free to fork this repository and submit pull requests with improvements or bug fixes.
