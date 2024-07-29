import http.server
import socketserver
import os
import random
import threading
import socket
import time
from urllib.parse import unquote

# Generate a random port number between 2000 and 9000
PORT = random.randint(1000, 9999)

# Flag to stop the server
stop_server_flag = False

# Function to get the local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't need to be reachable
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "123.232.00"
    finally:
        s.close()
    return local_ip

# Define the handler for serving directory listings and handling file downloads
class DirectoryListingHandler(http.server.SimpleHTTPRequestHandler):
    # Override the do_GET method to customize the response
    def do_GET(self):
        global stop_server_flag

        if self.path == '/shutdown':
            # Set the flag to stop the server
            stop_server_flag = True
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Server is shutting down...")
            return

        if self.path.startswith('/'):
            requested_file = unquote(self.path[1:])
            if os.path.isfile(requested_file):
                self.send_response(200)
                self.send_header('Content-Disposition', f'attachment; filename="{requested_file}"')
                self.end_headers()
                with open(requested_file, 'rb') as file:
                    self.wfile.write(file.read())
                return

        # Set the response status and headers
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Get the current directory
        current_dir = os.getcwd()

        # List all files and directories in the current directory
        files = os.listdir(current_dir)

        # Create an HTML page to display the directory listing
        html = """
        <html>
        <head>
            <title>HTTPSX</title>
            <link rel="icon" href="https://cdn.pixabay.com/photo/2013/07/12/15/53/network-150502_1280.png" type="image/png">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #fff; margin: 0; padding: 20px; }}
                h1 {{ color: #000; text-align: center; }}
                p {{ text-align: center; }}
                ul {{ list-style-type: none; padding: 0; text-align: center; }}
                li {{ padding: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>HTTPSX</h1>
            <p>Server Started At {port} port on {ip}</p>
            <h2>Files:</h2>
            <ul>
        """.format(ip=get_local_ip(), port=PORT)
        for file in files:
            html += f'<li><a href="/{file}">{file}</a></li>'
        html += """
            </ul>
        </body>
        </html>
        """

        # Send the HTML response
        self.wfile.write(html.encode('utf-8'))

def start_server():
    global stop_server_flag
    with socketserver.TCPServer(("0.0.0.0", PORT), DirectoryListingHandler) as httpd:
        local_ip = get_local_ip()
        print(f"Server started on port {PORT}")
        print(f"Access the web interface at: http://{local_ip}:{PORT}")
        print(f"To Shutdown running server, visit: http://{local_ip}:{PORT}/shutdown")

        while not stop_server_flag:
            httpd.handle_request()

        print("Server is stopping...")

# Run the server in a separate thread
server_thread = threading.Thread(target=start_server)
server_thread.start()

# Keep the server running for 5 hours (5 * 60 * 60 seconds)
time.sleep(5 * 60 * 60)

# Access the shutdown endpoint to stop the server
import requests
requests.get(f'http://localhost:{PORT}/shutdown')
server_thread.join()
