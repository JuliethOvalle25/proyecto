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

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(basedir, 'templates'),
    static_folder=os.path.join(basedir, 'static')
)
# Clave secreta     
app.secret_key = 'mi_clave_secreta_segura'




def obtener_conexion():
    try:
        print("📡 Intentando conectar a la base de datos PostgreSQL...")
        print("🔍 DB_HOST:", os.environ.get("DB_HOST"))
        print("🔍 DB_USER:", os.environ.get("DB_USER"))
        print("🔍 DB_NAME:", os.environ.get("DB_NAME"))
        print("🔍 DB_PORT:", os.environ.get("DB_PORT"))
        
        conn = psycopg2.connect(
            dbname="rayitos",
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            host="dpg-cvu6e0qdbo4c739eo8ng-a.oregon-postgres.render.com",
            port=os.environ.get("DB_PORT", "5432")
        )

        print("✅ Conexión establecida.")
        return conn
    except Exception as e:
        print("❌ Error de conexión:", str(e))
        return None





# Definir función de sesion como administrador 

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

   

   
   # 1. Inicio de sesión y registro
   
   
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        clave = request.form.get('clave')
        rol = request.form.get('rol')

        if not all([nombre, apellido, email, clave, rol]):
            return render_template('registro.html', error="Todos los campos son obligatorios.")

        connection = obtener_conexion()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (nombre, apellido, email, clave, rol)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, apellido, email, clave, rol))
            connection.commit()
            flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error al registrar: {e}", "danger")
        finally:
            cursor.close()
            connection.close()
    return render_template('registro.html')
   
   
   
   
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_nombre' in session:
        flash(f'Ya tienes una sesión activa como {session["usuario_nombre"]}.', 'info')
        return redirect(url_for('login' if session.get('usuario_rol') != 'administrador' else 'entidad'))

    if request.method == 'POST':
        email = request.form['email']
        clave = request.form['clave']
        connection = obtener_conexion()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s AND clave = %s", (email, clave))
            usuario = cursor.fetchone()
            if usuario:
                session['usuario_nombre'] = usuario[1]
                session['usuario_rol'] = usuario[5].strip().lower()
                flash(f'Bienvenido, {usuario[1]}!', 'success')
                return redirect(url_for('entidad') if session['usuario_rol'] == 'administrador' else url_for('empleado_areas'))
            else:
                flash("Correo o contraseña incorrectos", "danger")
        finally:
            cursor.close()
            connection.close()
    return render_template('login.html')

# 2. Cierre de sesión
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('login'))

# 3. Gestión de áreas
@app.route('/entidad')
def entidad():
    connection = obtener_conexion()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM area")
    areas = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('entidad.html', areas=areas)

@app.route('/crear_area', methods=['GET', 'POST'])
def crear_area():
    if request.method == 'POST':
        connection = obtener_conexion()
        nombre_area = request.form.get('nombre-area')
        elementos = request.form.getlist('elementos')
        area_data = {k: 1 if k.replace('_', ' ').capitalize() in elementos else 0 for k in [
            'pared','suelo','puerta','ventana','escritorio','mesas','sillas','sanitario','lavamanos','casa','rodadero','biblioteca','piscina_pelotas']}
        cursor = connection.cursor()
        query = """
            INSERT INTO area (nombre_area, pared, suelo, puerta, ventana, escritorio, mesas, sillas, sanitario, lavamanos, casa, rodadero, biblioteca, piscina_pelotas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            nombre_area,
            area_data['pared'], area_data['suelo'], area_data['puerta'], area_data['ventana'],
            area_data['escritorio'], area_data['mesas'], area_data['sillas'], area_data['sanitario'],
            area_data['lavamanos'], area_data['casa'], area_data['rodadero'],
            area_data['biblioteca'], area_data['piscina_pelotas']
        ))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('gestion_area'))
    return render_template('crear_area.html')

@app.route('/gestion_area')
def gestion_area():
    connection = obtener_conexion()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id_area, nombre_area,
            CASE WHEN pared = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN suelo = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN puerta = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN ventana = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN escritorio = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN mesas = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN sillas = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN sanitario = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN lavamanos = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN casa = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN rodadero = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN biblioteca = 1 THEN 'Si' ELSE NULL END,
            CASE WHEN piscina_pelotas = 1 THEN 'Si' ELSE NULL END
        FROM area
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('gestion_area.html', columns=columns, rows=rows)

@app.route('/eliminar_area/<int:id_area>', methods=['POST'])
def eliminar_area(id_area):
    connection = obtener_conexion()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM limpieza WHERE id_area = %s", (id_area,))
    cursor.execute("DELETE FROM area WHERE id_area = %s", (id_area,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('gestion_area'))

# 4. Edición de áreas
@app.route('/editar_area/<int:id_area>', methods=['GET', 'POST'])
def editar_area(id_area):
    connection = obtener_conexion()
    cursor = connection.cursor()

    if request.method == 'POST':
        nombre_area = request.form['nombre_area']
        elementos = request.form.getlist('elementos')

        cursor.execute("SELECT * FROM area WHERE id_area = %s", (id_area,))
        area = cursor.fetchone()

        if area:
            valores = lambda i, nombre: 1 if nombre in elementos else area[i]
            valores_dict = {
                'pared': valores(2, 'Pared'), 'suelo': valores(3, 'Suelo'), 'puerta': valores(4, 'Puerta'),
                'ventana': valores(5, 'Ventana'), 'escritorio': valores(6, 'Escritorio'), 'mesas': valores(7, 'Mesas'),
                'sillas': valores(8, 'Sillas'), 'sanitario': valores(9, 'Sanitario'), 'lavamanos': valores(10, 'Lavamanos'),
                'casa': valores(11, 'Casa'), 'rodadero': valores(12, 'Rodadero'), 'biblioteca': valores(13, 'Biblioteca'),
                'piscina_pelotas': valores(14, 'Piscina pelotas')
            }

            update_query = """
                UPDATE area SET nombre_area = %s, pared = %s, suelo = %s, puerta = %s, ventana = %s,
                escritorio = %s, mesas = %s, sillas = %s, sanitario = %s, lavamanos = %s, casa = %s,
                rodadero = %s, biblioteca = %s, piscina_pelotas = %s WHERE id_area = %s
            """

            cursor.execute(update_query, (
                nombre_area,
                valores_dict['pared'], valores_dict['suelo'], valores_dict['puerta'], valores_dict['ventana'],
                valores_dict['escritorio'], valores_dict['mesas'], valores_dict['sillas'], valores_dict['sanitario'],
                valores_dict['lavamanos'], valores_dict['casa'], valores_dict['rodadero'],
                valores_dict['biblioteca'], valores_dict['piscina_pelotas'], id_area
            ))
            connection.commit()
            flash('Área actualizada correctamente', 'success')

        cursor.close()
        connection.close()
        return redirect(url_for('gestion_area'))

    else:
        cursor.execute("SELECT * FROM area WHERE id_area = %s", (id_area,))
        area = cursor.fetchone()

        if not area:
            flash("El área no fue encontrada.", "danger")
            return redirect(url_for('gestion_area'))

        elementos = [
            'Pared' if area[2] else '', 'Suelo' if area[3] else '', 'Puerta' if area[4] else '',
            'Ventana' if area[5] else '', 'Escritorio' if area[6] else '', 'Mesas' if area[7] else '',
            'Sillas' if area[8] else '', 'Sanitario' if area[9] else '', 'Lavamanos' if area[10] else '',
            'Casa' if area[11] else '', 'Rodadero' if area[12] else '', 'Biblioteca' if area[13] else '',
            'Piscina pelotas' if area[14] else ''
        ]
        elementos = [e for e in elementos if e]

        cursor.close()
        connection.close()

        return render_template('editar_area.html', area=area, elementos=elementos)

# 5. Funcionalidad para empleados
@app.route('/empleado/areas', methods=['GET', 'POST'])
def empleado_areas():
    connection = obtener_conexion()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id_area, nombre_area FROM area")
        areas = cursor.fetchall()

        fecha_actual = datetime.today().strftime('%Y-%m-%d')

        if request.method == 'GET':
            id_area = request.args.get('id_area')
            if not id_area:
                return render_template('empleado_areas.html', areas=areas, elementos={}, usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual)

            cursor.execute("SELECT pared, suelo, puerta, ventana, escritorio, mesas, sillas, sanitario, lavamanos, casa, rodadero, biblioteca, piscina_pelotas FROM area WHERE id_area = %s", (int(id_area),))
            area_seleccionada = cursor.fetchone()

            elementos = {}
            if area_seleccionada:
                etiquetas = ['pared', 'suelo', 'puerta', 'ventana', 'escritorio', 'mesas', 'sillas', 'sanitario', 'lavamanos', 'casa', 'rodadero', 'biblioteca', 'piscina_pelotas']
                elementos = dict(zip(etiquetas, area_seleccionada))

            return render_template('empleado_areas.html', areas=areas, elementos=elementos, usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual)

        elif request.method == 'POST':
            id_area = request.form.get('id_area')
            fue_limpio = request.form.getlist('fue_limpio[]')
            observaciones = request.form.get('observaciones', '')

            query_insert = """
            INSERT INTO limpieza (id_area, responsable, elemento, fue_limpio, fecha, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            if fue_limpio:
                for elemento in fue_limpio:
                    cursor.execute(query_insert, (
                        int(id_area),
                        session.get('usuario_nombre', 'Desconocido'),
                        elemento,
                        1,
                        fecha_actual,
                        observaciones or '',
                    ))
                connection.commit()
            return redirect(url_for('empleado_areas'))

    finally:
        cursor.close()
        connection.close()

# 6. Reportes
@app.route('/reportes', methods=['GET'])
def reportes():
    connection = obtener_conexion()
    cursor = connection.cursor()

    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    responsable = request.args.get('responsable')
    area = request.args.get('area')

    try:
        query = """
            SELECT TO_CHAR(l.fecha, 'DD/MM/YYYY'), l.id_area, a.nombre_area,
                   l.responsable, l.elemento, l.fue_limpio, l.observaciones
            FROM limpieza l
            JOIN area a ON l.id_area = a.id_area
            WHERE 1=1
        """
        filtros = []

        if fecha_inicio:
            query += " AND l.fecha >= TO_DATE(%s, 'YYYY-MM-DD')"
            filtros.append(fecha_inicio)

        if fecha_fin:
            query += " AND l.fecha <= TO_DATE(%s, 'YYYY-MM-DD')"
            filtros.append(fecha_fin)

        if responsable:
            query += " AND LOWER(l.responsable) LIKE LOWER(%s)"
            filtros.append(f"%{responsable}%")

        if area:
            query += " AND LOWER(a.nombre_area) LIKE LOWER(%s)"
            filtros.append(f"%{area}%")

        query += " ORDER BY l.fecha"
        cursor.execute(query, filtros)
        resultados = cursor.fetchall()

        reportes_agrupados = {}
        for fila in resultados:
            fecha = fila[0]
            if fecha not in reportes_agrupados:
                reportes_agrupados[fecha] = []
            reportes_agrupados[fecha].append(fila)

    finally:
        cursor.close()
        connection.close()

    return render_template('reportes.html', reportes_agrupados=reportes_agrupados)

# 7. Generar PDF
@app.route('/generar_pdf', methods=['GET'])
def generar_pdf():
    connection = obtener_conexion()
    cursor = connection.cursor()

    try:
        query = """
            SELECT l.fecha, a.nombre_area, l.responsable, l.elemento, l.fue_limpio, l.observaciones
            FROM limpieza l
            JOIN area a ON l.id_area = a.id_area
        """
        cursor.execute(query)
        reportes = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []

    logo_path = "app/static/images/Logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=100, height=50)
        elements.append(logo)

    styles = getSampleStyleSheet()
    title = Paragraph("Reporte de Limpieza", styles['Title'])
    elements.append(title)

    data = [["Fecha", "Área", "Responsable", "Elemento", "¿Fue Limpio?", "Observaciones"]]

    for reporte in reportes:
        data.append([
            reporte[0].strftime("%d/%m/%Y"),
            reporte[1],
            reporte[2],
            reporte[3],
            "Sí" if reporte[4] else "No",
            reporte[5] or ""
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Firma del Responsable:", styles['Normal']))
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("_______________________", styles['Normal']))
    elements.append(Paragraph("Nombre del Responsable", styles['Normal']))

    doc.build(elements)
    output.seek(0)

    return Response(
        output,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=reporte_limpieza.pdf"}
    )

# 8. Gestión de usuarios
@app.route('/gestion_usuario')
def gestion_usuario():
    connection = obtener_conexion()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nombre, apellido, email, rol FROM usuarios")
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('gestion_usuario.html', columns=columns, rows=rows)

@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    connection = obtener_conexion()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('gestion_usuario'))

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    connection = obtener_conexion()
    cursor = connection.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT id, nombre, apellido, email, rol FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        if not usuario:
            flash("Usuario no encontrado", "danger")
            return redirect(url_for('gestion_usuario'))
        return render_template('editar_usuario.html', usuario=usuario)

    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        rol = request.form.get('rol')

        try:
            cursor.execute("""
                UPDATE usuarios
                SET nombre = %s, apellido = %s, email = %s, rol = %s
                WHERE id = %s
            """, (nombre, apellido, email, rol, id))
            connection.commit()
            flash("Usuario actualizado correctamente", "success")
        except Exception as e:
            flash(f"Error al actualizar usuario: {e}", "danger")
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('gestion_usuario'))
    
    

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




