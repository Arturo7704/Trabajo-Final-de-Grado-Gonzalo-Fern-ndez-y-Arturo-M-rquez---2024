from flask import Flask, send_file
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/run_script')
def run_script():
    subprocess.Popen(['python', 'prueba.py'])
    return 'Script ejecutado con éxito'

@app.route('/prueba.py')
def execute_prueba_py():
    subprocess.Popen(['python', 'prueba.py'])
    return 'Script ejecutado con éxito'

if __name__ == '__main__':
    # Ejecutar la aplicación Flask en la IP de tu máquina virtual específica (192.168.57.129)
    app.run(host='192.168.57.129', port=5000, debug=True)
