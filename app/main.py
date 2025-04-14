from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import datetime
from datetime import date
from flask import Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
print("✅ DB_HOST cargado:", os.environ.get("DB_HOST"))


# Crear la aplicación Flask

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
# Clave secreta     
app.secret_key = 'mi_clave_secreta_segura'




def obtener_conexion():
    try:
        return psycopg2.connect(
            dbname="rayitos",
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT", "5432")
        )
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None





# Definir función de sesion como administrador 
'''''
def es_Administrador():
    return 'rol' in session and session['rol'] == 'Administrador'  # Verifica si el usuario está en sesión y si su rol es 'administrador'

def es_Empleado():
    # Verifica si el usuario está autenticado y si su rol es 'Empleado'
    if 'usuario' in session:
        connection = obtener_conexion()
        cursor = connection.cursor()

        cursor.execute("SELECT rol FROM usuarios WHERE id = :id", [session['usuario']])
        rol = cursor.fetchone()

        cursor.close()
        connection.close()

        if rol and rol[0] == 'Empleado':  # Verifica si el rol es 'Empleado'
            return True

    return False  # Si no está logueado o el rol no es 'Empleado', retorna False



def obtener_areas(cursor):
    try:
        query = "SELECT id_area, nombre_area FROM area ORDER BY nombre_area"
        cursor.execute(query)
        areas = cursor.fetchall()
        return areas
    except Exception as e:
        print("Error al obtener las áreas:", e)
        return []

'''

## PÁGINAS SIN FUNCIONALIDAD

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/servicios')
def servicios():
    return render_template('servicios.html')

@app.route('/metodologia')
def metodologia():
    return render_template('metodologia.html')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

@app.route('/entidad_admin')
def entidad_admin():
    return render_template('entidad_admin.html')



## FUNCIONALIDAD DE LA PÁGINA

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Obtén los valores del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        clave = request.form.get('clave')
        rol = request.form.get('rol')

        print(f"Datos recibidos: Nombre={nombre}, Apellido={apellido}, Email={email}, Clave={clave}, Rol={rol}")

        if not all([nombre, apellido, email, clave, rol]):
            return render_template('registro.html', error="Todos los campos son obligatorios.")
        
        try:
            connection = obtener_conexion()
            if connection is None:
                return render_template('registro.html', error="No se pudo conectar a la base de datos.")
            
            cursor = connection.cursor()

            # El id ya es SERIAL, no hace falta incluirlo
            query = """
                INSERT INTO usuarios (nombre, apellido, email, clave, rol) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, apellido, email, clave, rol))
            connection.commit()

            print("Usuario registrado exitosamente.")
            
            cursor.close()
            connection.close()
            
            return redirect(url_for('login'))
        
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            return render_template('registro.html', error="Hubo un problema al registrar el usuario.")
        
    return render_template('registro.html')



## CREACION DE TABLAS EN POSTGREESQL

def crear_tablas():
    conexion = obtener_conexion()
    if conexion is None:
        print("No se pudo conectar a la base de datos para crear las tablas.")
        return

    try:
        cursor = conexion.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS area (
            id_area SERIAL PRIMARY KEY,
            nombre_area VARCHAR(100),
            pared SMALLINT CHECK (pared IN (0, 1)),
            suelo SMALLINT CHECK (suelo IN (0, 1)),
            puerta SMALLINT CHECK (puerta IN (0, 1)),
            ventana SMALLINT CHECK (ventana IN (0, 1)),
            escritorio SMALLINT CHECK (escritorio IN (0, 1)),
            mesas SMALLINT CHECK (mesas IN (0, 1)),
            sillas SMALLINT CHECK (sillas IN (0, 1)),
            sanitario SMALLINT CHECK (sanitario IN (0, 1)),
            lavamanos SMALLINT CHECK (lavamanos IN (0, 1)),
            casa SMALLINT CHECK (casa IN (0, 1)),
            rodadero SMALLINT CHECK (rodadero IN (0, 1)),
            biblioteca SMALLINT CHECK (biblioteca IN (0, 1)),
            piscina_pelotas SMALLINT CHECK (piscina_pelotas IN (0, 1))
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS limpieza (
            id SERIAL PRIMARY KEY,
            id_area INTEGER NOT NULL,
            responsable VARCHAR(100) NOT NULL,
            elemento VARCHAR(100) NOT NULL,
            fue_limpio SMALLINT NOT NULL CHECK (fue_limpio IN (0, 1)),
            fecha DATE NOT NULL,
            observaciones VARCHAR(500),
            CONSTRAINT fk_limpieza_area FOREIGN KEY (id_area) REFERENCES area(id_area) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50),
            apellido VARCHAR(50),
            email VARCHAR(100),
            clave VARCHAR(100),
            rol VARCHAR(20)
        );
        """)

        conexion.commit()
        print("Tablas creadas correctamente.")
        cursor.close()
        conexion.close()

    except Exception as e:
        print(f"Error al crear las tablas: {e}")



if __name__ == '__main__':
    crear_tablas()
    app.run(debug=True)




