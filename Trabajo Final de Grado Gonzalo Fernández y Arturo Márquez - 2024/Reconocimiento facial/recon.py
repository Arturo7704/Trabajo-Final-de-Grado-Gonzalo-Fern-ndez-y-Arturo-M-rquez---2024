import os
import cv2
import smtplib
import mysql.connector
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import face_recognition
import sys
import webbrowser
from dotenv import load_dotenv

load_dotenv()

# Variables globales
base_de_datos_path_admin = "administradores"
base_de_datos_path_usuarios = "usuarios_normales"
nombres_admin = []
nombres_usuarios = []
caras_conocidas_admin = []
caras_conocidas_usuarios = []
foto_desconocido_path = "foto_desconocido.jpg"
correo_destinatario = "gony.oficial@gmail.com"
correo_remitente = "gony11.oficial@gmail.com"
password_remitente = os.getenv("PASSWORD")
connection = None
datos_insertados = False
persona_desconocida_detectada = False  # Bandera para controlar detección de desconocidos

# Crear carpetas si no existen
os.makedirs(base_de_datos_path_admin, exist_ok=True)
os.makedirs(base_de_datos_path_usuarios, exist_ok=True)

def cargar_base_de_datos():
    global connection
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='reconocimiento_facial',
            user='root',
            password=''
        )

        if connection.is_connected():
            print("Conexión exitosa a MySQL")
    except OSError as e:
        print(f"Error de conexión a MySQL: {e}")

    # Cargar imágenes de la carpeta de administradores
    for nombre_archivo in os.listdir(base_de_datos_path_admin):
        if nombre_archivo.endswith(".jpg") or nombre_archivo.endswith(".png"):
            nombre = os.path.splitext(nombre_archivo)[0]
            nombres_admin.append(nombre)

            # Cargar la imagen y obtener la codificación facial
            imagen_path = os.path.join(base_de_datos_path_admin, nombre_archivo)
            imagen = face_recognition.load_image_file(imagen_path)
            codificacion = face_recognition.face_encodings(imagen)[0]
            caras_conocidas_admin.append(codificacion)

    # Cargar imágenes de la carpeta de usuarios normales
    for nombre_archivo in os.listdir(base_de_datos_path_usuarios):
        if nombre_archivo.endswith(".jpg") or nombre_archivo.endswith(".png"):
            nombre = os.path.splitext(nombre_archivo)[0]
            nombres_usuarios.append(nombre)

            # Cargar la imagen y obtener la codificación facial
            imagen_path = os.path.join(base_de_datos_path_usuarios, nombre_archivo)
            imagen = face_recognition.load_image_file(imagen_path)
            codificacion = face_recognition.face_encodings(imagen)[0]
            caras_conocidas_usuarios.append(codificacion)

def capturar_foto_desconocido(frame, face_location):
    # Recortar la imagen de la cara desconocida
    top, right, bottom, left = face_location
    cara_desconocida = frame[top:bottom, left:right]

    # Guardar la imagen de la cara desconocida
    cv2.imwrite(foto_desconocido_path, cara_desconocida)
    print("Foto de la cara de la persona desconocida guardada.")

def enviar_correo_con_foto():
    # Configurar el correo electrónico
    msg = MIMEMultipart()
    msg['From'] = correo_remitente
    msg['To'] = correo_destinatario
    msg['Subject'] = "Persona Desconocida Detectada"

    # Adjuntar la imagen al correo
    with open(foto_desconocido_path, 'rb') as fp:
        img = MIMEImage(fp.read())
    msg.attach(img)

    # Enviar el correo utilizando SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(correo_remitente, password_remitente)
        smtp.send_message(msg)
    print("Correo electrónico enviado con la foto de la persona desconocida.")

def iniciar_captura_video():
    global connection
    global datos_insertados
    global persona_desconocida_detectada
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        caras_detectadas = face_recognition.face_locations(frame)
        codificaciones_detectadas = face_recognition.face_encodings(frame, caras_detectadas)

        # Bandera para indicar si se ha detectado un usuario conocido
        usuario_reconocido = False

        for codificacion_detectada, (top, right, bottom, left) in zip(codificaciones_detectadas, caras_detectadas):
            coincidencias_admin = face_recognition.compare_faces(caras_conocidas_admin, codificacion_detectada)
            coincidencias_usuarios = face_recognition.compare_faces(caras_conocidas_usuarios, codificacion_detectada)

            nombre_persona = "Desconocido"
            hora = datetime.now().strftime("%H:%M:%S")

            # Verificar si el rostro pertenece a un administrador
            if True in coincidencias_admin:
                indice_coincidencia = coincidencias_admin.index(True)
                nombre_persona = nombres_admin[indice_coincidencia]

                # Mostrar un mensaje cerca de la cara reconocida
                mensaje = f"Administrador reconocido: {nombre_persona}. Presiona Enter para continuar"
                cv2.putText(frame, mensaje, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                usuario_reconocido = True

                # Verificar conexión antes de usarla
                if connection is not None and connection.is_connected() and not datos_insertados:
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO personas (nombre) VALUES (%s)", (nombre_persona,))
                    connection.commit()
                    print("Datos insertados correctamente en la base de datos")
                    cursor.close()
                    datos_insertados = True  # Establecer la variable en True para indicar que ya se han insertado datos
                
                # Esperar a que el usuario presione Enter para proceder
                key = cv2.waitKey(1)
                if key == 13:  # 13 es el código ASCII para la tecla Enter
                    webbrowser.open('http://localhost/administrador.html')
                    sys.exit()

            # Verificar si el rostro pertenece a un usuario normal
            elif True in coincidencias_usuarios:
                indice_coincidencia = coincidencias_usuarios.index(True)
                nombre_persona = nombres_usuarios[indice_coincidencia]

                # Mostrar un mensaje cerca de la cara reconocida
                mensaje = f"Usuario normal reconocido: {nombre_persona}. Presiona Enter para continuar"
                cv2.putText(frame, mensaje, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                usuario_reconocido = True

                # Verificar conexión antes de usarla
                if connection is not None and connection.is_connected() and not datos_insertados:
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO personas (nombre) VALUES (%s)",  (nombre_persona,))
                    connection.commit()
                    print("Datos insertados correctamente en la base de datos")
                    cursor.close()
                    datos_insertados = True  # Establecer la variable en True para indicar que ya se han insertado datos
                
                # Esperar a que el usuario presione Enter para proceder
                key = cv2.waitKey(1)
                if key == 13:  # 13 es el código ASCII para la tecla Enter
                    webbrowser.open('http://192.168.57.129:5001/')
                    sys.exit()

            else:
                if not persona_desconocida_detectada:
                    persona_desconocida_detectada = True
                    print("Persona desconocida detectada.")
                    # Capturar la foto de la persona desconocida
                    capturar_foto_desconocido(frame, (top, right, bottom, left))

            # Dibujar un rectángulo alrededor de la cara reconocida
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            # Mostrar el nombre y la hora debajo de la cara
            cv2.putText(frame, f"{nombre_persona} - {hora}", (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow('Reconocimiento Facial', frame)

        # Salir del bucle si se presiona la tecla Esc (27 en ASCII)
        key = cv2.waitKey(1)
        if key & 0xFF == 27:
            break

        # Enviar correo y resetear la bandera cuando se presiona Enter y hay un desconocido
        if key == 13 and persona_desconocida_detectada:  # 13 es el código ASCII para la tecla Enter
            enviar_correo_con_foto()
            persona_desconocida_detectada = False

    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()

    # Cerrar la conexión a la base de datos si está abierta
    if connection is not None and connection.is_connected():
        connection.close()

def main():
    cargar_base_de_datos()
    iniciar_captura_video()

if __name__ == "__main__":
    main()
