import smtplib
import keyboard

# Configura los detalles del correo
smtp_server = 'smtp.gmail.com'  # Por ejemplo, si usas Gmail
smtp_port = 587
sender_email = 'gony11.oficial@gmail.com'
sender_password = 'vhre dqap nwks dpws'
receiver_email = 'gony.oficial@gmail.com'
subject = 'Hola'
message = 'Hola'

# Función para enviar el correo
def send_email():
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            email_message = f'Subject: {subject}\n\n{message}'
            server.sendmail(sender_email, receiver_email, email_message)
            print("Correo enviado con éxito")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

# Configura el listener para la tecla Enter
def on_enter(event):
    send_email()

# Detectar la tecla Enter
keyboard.on_press_key("enter", on_enter)

print("Presiona Enter para enviar el correo...")

# Mantener el script corriendo
keyboard.wait('esc')  # Puedes cambiar 'esc' por otra tecla para detener el script
