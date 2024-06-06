from flask import Flask, send_file
import subprocess
import logging

app = Flask(__name__)

# Configurar el sistema de registro
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def index():
    logging.info('Se ha accedido a la página de inicio')
    return app.send_static_file('index.html')

@app.route('/run_script')
def run_script():
    logging.info('Se ha ejecutado el script')
    subprocess.Popen(['bash', 'curl.sh'])
    return 'Script ejecutado con éxito'

@app.route('/curl.sh')
def execute_prueba_py():
    logging.info('Se ha ejecutado el script curl.sh')
    subprocess.Popen(['bash', 'curl.sh'])
    return 'Script ejecutado con éxito'

if __name__ == '__main__':
    # Ejecutar la aplicación Flask en la IP de tu máquina virtual específica (192.168.57.129)
    app.run(host='192.168.57.129', port=5000, debug=True)
