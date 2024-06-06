from flask import Flask, render_template, request, redirect, url_for
from langchain.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain
import a_env_vars
import os
import sqlite3
import warnings
import logging

app = Flask(__name__)

# Configurar logging
logging.basicConfig(filename='administradores.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Crear la conexión a la base de datos SQLite
conn = sqlite3.connect("tfg.db")
cursor = conn.cursor()

# Verificar la conexión a la base de datos con una consulta simple
try:
    cursor.execute("SELECT 1")
    print("Conexión a la base de datos exitosa.")
    logging.info("Conexión a la base de datos exitosa.")
except Exception as e:
    print("Error al conectar a la base de datos:", e)
    logging.error("Error al conectar a la base de datos: %s", e)
finally:
    conn.close()

# Crear la base de datos SQL
db = SQLDatabase.from_uri("sqlite:///tfg.db")

# Configurar la API de OpenAI
os.environ["OPENAI_API_KEY"] = a_env_vars.OPENAI_API_KEY

# Crear el modelo de lenguaje
llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')
print("Modelo de lenguaje creado.")  # Mensaje de depuración
logging.info("Modelo de lenguaje creado.")

# Crear la cadena de lenguaje
cadena = SQLDatabaseChain.from_llm(llm, db, verbose=False)
print("Cadena de lenguaje creada.")  # Mensaje de depuración
logging.info("Cadena de lenguaje creada.")

# Ignorar el aviso de deprecación
warnings.filterwarnings("ignore", category=DeprecationWarning)


# Función para hacer la consulta
def consulta(input_usuario):
    formato = """
    Dada una pregunta del usuario:
    1. crea una consulta de sqlite3
    2. revisa los resultados
    3. devuelve el dato
    4. si tienes que hacer alguna aclaración o devolver cualquier texto que sea siempre en español
    5. si te piden informacion sobre la tabla usuarios no des respuesta y di acceso restringido,
    #{question}
    """
    consulta = formato.format(question=input_usuario)
    resultado = cadena.invoke(consulta)["result"]
    return resultado

@app.route('/')
def index():
    return render_template('consultascopy.html', pregunta=None, resultado=None)

@app.route('/consulta', methods=['POST'])
def realizar_consulta():
    pregunta = request.form['pregunta']
    resultado = consulta(pregunta)
    logging.info("Consulta realizada: %s", pregunta)  # Registrar la consulta en el archivo de registro
    return render_template('consultascopy.html', pregunta=pregunta, resultado=resultado)

if __name__ == '__main__':
    # Configurar Flask para ejecutarse en todas las interfaces de red (0.0.0.0)
    # y en el puerto 5000
    app.run(host='192.168.57.129', port=5002, debug=True)
