import threading
import serial
import serial.tools.list_ports
import json
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from datetime import datetime
import pytz
import time

app = Flask(__name__)

# Conexión a MongoDB
uri = "mongodb+srv://casallasmariana912:NinayZoe14@cluster0.ew61uxo.mongodb.net/"
client = MongoClient(uri)
db = client["proyecto"]
coleccion = db["proyecto1"]

# Zona horaria
timezone = pytz.timezone('America/Bogota')

# Puerto y baudrate
puerto_serial = 'COM5'  # Cambia este valor si es necesario
baudrate = 9600

# Intentar abrir el puerto serial
try:
    ser = serial.Serial(puerto_serial, baudrate, timeout=2)
    print(f"Puerto {puerto_serial} abierto correctamente.")
except serial.SerialException as e:
    print(f"Error al abrir el puerto {puerto_serial}: {e}")
    ser = None  # Evita que el hilo se inicie si no hay puerto

# Función para leer datos del Arduino y guardarlos en MongoDB
def leer_datos_arduino():
    if not ser:
        print("Puerto serial no disponible. No se puede iniciar la lectura.")
        return

    while True:
        try:
            linea = ser.readline().decode('utf-8').strip()
            if linea:
                print("Recibido:", linea)
                data = json.loads(linea)
                data["timestamp"] = datetime.now(timezone)
                coleccion.insert_one(data)
                print("Guardado en MongoDB:", data)
        except json.JSONDecodeError:
            print("Error: línea recibida no es JSON válido:", linea)
        except Exception as e:
            print("Error al procesar:", e)
        time.sleep(0.1)  # Pausa para evitar sobrecarga

# Iniciar hilo para leer los datos del Arduino
if ser:
    thread = threading.Thread(target=leer_datos_arduino)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    return render_template('index.html')  # Asegúrate de tener index.html en /templates

@app.route('/get_data')
def get_data():
    # Obtener los últimos 20 documentos y ordenarlos por timestamp ascendente
    documentos = coleccion.find().sort("timestamp", -1).limit(20)
    documentos = reversed(list(documentos))  # Invertimos para mantener orden cronológico

    datos = []
    for doc in documentos:
        datos.append({
            "_id": str(doc["_id"]),
            "temperatura": doc.get("temperature"),
            "humedad": doc.get("humidity"),
            "timestamp": doc["timestamp"].isoformat() if "timestamp" in doc else None
        })

    return jsonify(datos)

if __name__ == '__main__':
    app.run(debug=True)
