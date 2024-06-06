from http.server import SimpleHTTPRequestHandler, HTTPServer
import subprocess

class MyHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        # Al recibir un comando POST, ejecuta el script deseado
        if self.path == "/execute":
            subprocess.run(["python", "C:\\Users\\gonyf\\Desktop\\Nebrija\\Reconocimiento facial\\prueba2.py"])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Script ejecutado")

server = HTTPServer(("0.0.0.0", 8080), MyHandler)
server.serve_forever()
