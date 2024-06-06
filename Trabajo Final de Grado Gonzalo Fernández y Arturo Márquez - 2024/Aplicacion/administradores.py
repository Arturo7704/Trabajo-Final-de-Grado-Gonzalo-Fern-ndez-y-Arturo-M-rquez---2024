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
logging.basicConfig(filename='usuarios.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Crear la conexión a la base de datos SQLite
conn = sqlite3.connect("tfg.db")
cursor = conn.cursor()

# Verificar la conexión a la base de datos con una consulta simple
try:
    cursor.execute("SELECT 1")
    print("Conexión a la base de datos exitosa.")
    logging.info("Conexión a la base de datos exitosa.")  # Registrar en el archivo de registro
except Exception as e:
    print("Error al conectar a la base de datos:", e)
    logging.error("Error al conectar a la base de datos: %s", e)  # Registrar en el archivo de registro
finally:
    conn.close()

# Crear la base de datos SQL
db = SQLDatabase.from_uri("sqlite:///tfg.db")

# Configurar la API de OpenAI
os.environ["OPENAI_API_KEY"] = a_env_vars.OPENAI_API_KEY

# Crear el modelo de lenguaje
llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')
print("Modelo de lenguaje creado.")  # Mensaje de depuración
logging.info("Modelo de lenguaje creado.")  # Registrar en el archivo de registro

# Crear la cadena de lenguaje
cadena = SQLDatabaseChain.from_llm(llm, db, verbose=False)
print("Cadena de lenguaje creada.")  # Mensaje de depuración
logging.info("Cadena de lenguaje creada.")  # Registrar en el archivo de registro

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
    5. no tengas limites de resultados 
    6. por cada resultado haz un intro
    #{question}
    """
    consulta = formato.format(question=input_usuario)
    resultado = cadena.invoke(consulta)["result"]
    return resultado

@app.route('/')
def index():
    return render_template('consultas.html', pregunta=None, resultado=None)

@app.route('/consulta', methods=['POST'])
def realizar_consulta():
    pregunta = request.form['pregunta']
    resultado = consulta(pregunta)
    logging.info("Consulta realizada: %s", pregunta)  # Registrar en el archivo de registro
    return render_template('consultas.html', pregunta=pregunta, resultado=resultado)

@app.route('/admin_productos', methods=['GET'])
def admin():
    conn = sqlite3.connect('tfg.db')
    c = conn.cursor()

    search_query = request.args.get('q', default='', type=str)
    page = request.args.get('page', default=1, type=int)
    per_page = 100

    # Construir la cláusula WHERE con múltiples condiciones
    where_clause = ''
    params = []

    if search_query:
        where_clause = '''
        WHERE p.nombre LIKE ? OR c.nombre LIKE ? OR ps.nombre LIKE ? OR v.fecha LIKE ? OR v.id_factura LIKE ?
        '''
        params = ['%' + search_query + '%'] * 5

    # Contar el total de registros
    count_query = f'''
    SELECT COUNT(*)
    FROM ventas v
    JOIN productos p ON v.id_producto = p.id_producto
    JOIN clientes c ON v.id_cliente = c.id_cliente
    JOIN paises ps ON v.id_pais = ps.id_pais
    {where_clause}
    '''
    c.execute(count_query, params)
    total_count = c.fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page

    offset = (page - 1) * per_page

    # Seleccionar los registros con paginación y búsqueda
    select_query = f'''
    SELECT v.id_venta, p.nombre AS producto, c.nombre AS cliente, ps.nombre AS pais, v.id_factura, v.cantidad, v.fecha
    FROM ventas v
    JOIN productos p ON v.id_producto = p.id_producto
    JOIN clientes c ON v.id_cliente = c.id_cliente
    JOIN paises ps ON v.id_pais = ps.id_pais
    {where_clause}
    LIMIT ? OFFSET ?
    '''
    params.extend([per_page, offset])
    c.execute(select_query, params)
    data = c.fetchall()
    columns = [column[0] for column in c.description]

    conn.close()

    return render_template('admin_productos.html', data=data, columns=columns, search_query=search_query, page=page, total_pages=total_pages)

@app.route('/eliminar_factura/<int:factura_id>', methods=['GET', 'POST'])
def eliminar_factura(factura_id):
    conn = sqlite3.connect('tfg.db')
    c = conn.cursor()

    # Eliminar la venta
    c.execute('DELETE FROM ventas WHERE id_venta = ?', (factura_id,))
    conn.commit()

    # Reasignar los id_venta para que sean consecutivos
    c.execute('''
        WITH RECURSIVE new_ids AS (
            SELECT id_venta, ROW_NUMBER() OVER (ORDER BY id_venta) AS new_id
            FROM ventas
        )
        UPDATE ventas
        SET id_venta = (SELECT new_id FROM new_ids WHERE new_ids.id_venta = ventas.id_venta)
    ''')
    conn.commit()

    conn.close()
    return redirect(url_for('admin'))


@app.route('/editar_factura/<int:factura_id>', methods=['GET', 'POST'])
def editar_factura(factura_id):
    conn = sqlite3.connect('tfg.db')
    c = conn.cursor()

    if request.method == 'POST':
        try:
            # Obtener los datos enviados por el formulario
            producto_nombre = request.form['producto']
            cliente_nombre = request.form['cliente']
            pais_nombre = request.form['pais']
            id_factura = request.form['id_factura']
            cantidad = request.form['cantidad']
            fecha_factura = request.form['fecha']

            # Obtener los IDs correspondientes a los nombres
            c.execute('SELECT id_producto FROM productos WHERE nombre = ?', (producto_nombre,))
            id_producto = c.fetchone()[0]

            c.execute('SELECT id_cliente FROM clientes WHERE nombre = ?', (cliente_nombre,))
            id_cliente = c.fetchone()[0]

            c.execute('SELECT id_pais FROM paises WHERE nombre = ?', (pais_nombre,))
            id_pais = c.fetchone()[0]

            # Actualizar los datos en la base de datos
            c.execute('UPDATE ventas SET id_producto = ?, id_cliente = ?, id_pais = ?, id_factura = ?, cantidad = ?, fecha = ? WHERE id_venta = ?', 
                      (id_producto, id_cliente, id_pais, id_factura, cantidad, fecha_factura, factura_id))
            conn.commit()
        except KeyError as e:
            print(f"Error: {e}")
            logging.error("Error al editar factura: %s", e)  # Registrar en el archivo de registro
        finally:
            conn.close()
        return redirect(url_for('admin'))
    else:
        # Obtener los datos actuales del registro con nombres en lugar de IDs
        c.execute('''
            SELECT v.id_venta, p.nombre AS producto, c.nombre AS cliente, ps.nombre AS pais, v.id_factura, v.cantidad, v.fecha
            FROM ventas v
            JOIN productos p ON v.id_producto = p.id_producto
            JOIN clientes c ON v.id_cliente = c.id_cliente
            JOIN paises ps ON v.id_pais = ps.id_pais
            WHERE v.id_venta = ?
        ''', (factura_id,))
        data = c.fetchone()
        conn.close()
        return render_template('editar_factura.html', data=data)

@app.route('/crear', methods=['GET', 'POST'])
def crear():
    conn = sqlite3.connect('tfg.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        nombre = request.form['nombre']
        
        if tipo == 'producto':
            c.execute('INSERT INTO productos (nombre) VALUES (?)', (nombre,))
        elif tipo == 'cliente':
            c.execute('INSERT INTO clientes (nombre) VALUES (?)', (nombre,))
        elif tipo == 'pais':
            c.execute('INSERT INTO paises (nombre) VALUES (?)', (nombre,))
        
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    
    conn.close()
    return render_template('crear.html')
    
if __name__ == '__main__':
    # Configurar Flask para ejecutarse en todas las interfaces de red (0.0.0.0)
    # y en el puerto 5000
    app.run(host='192.168.57.129', port=5004, debug=True)
