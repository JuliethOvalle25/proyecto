
import oracledb
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


# Crear la aplicación Flask
app = Flask(__name__)
# Clave secreta     
app.secret_key = 'mi_clave_secreta_segura'


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





# Configuración conexión a base de datos rayitos
dsn = "localhost:1521/xe"
usuario = "sys"
contraseña = "123"

def obtener_conexion():
    try:
        # Establecer conexión con la base de datos Oracle
        connection = oracledb.connect(
            user="sys",                 # Nombre de usuario
            password="123",             # contraseña
            dsn="190.26.141.106",    # cadena de conexión
            mode=oracledb.AUTH_MODE_SYSDBA  # Incluir por que uso  SYS
        )
        print("Conexión exitosa a la base de datos.")
        return connection

    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"Error al conectar con la base de datos: {error.message}")
        return None





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
            query = """
                INSERT INTO usuarios (id, nombre, apellido, email, clave, rol) 
                VALUES (usuarios_seq.NEXTVAL, :nombre, :apellido, :email, :clave, :rol)
            """
            cursor.execute(query, {
                'nombre': nombre,
                'apellido': apellido,
                'email': email,
                'clave': clave,
                'rol': rol
            })
            connection.commit()
            print("Usuario registrado exitosamente.")
            
            cursor.close()
            connection.close()
            
            return redirect(url_for('login'))
        
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            return render_template('registro.html', error="Hubo un problema al registrar el usuario.")
        
    return render_template('registro.html')



## Función para que el usuario se pueda logear o registrar uno nuevo.


@app.route('/login', methods=['GET', 'POST'])
def login():
    
        if 'usuario_nombre' in session:
            flash(f'Ya tienes una sesión activa como {session["usuario_nombre"]}. Cierra la sesión actual para iniciar otra.', 'info')
            return redirect(url_for('login' if session.get('usuario_rol') != 'administrador' else 'entidad'))
    
    
        if request.method == 'POST':
            email = request.form['email']
            clave = request.form['clave']

            connection = obtener_conexion()
            cursor = connection.cursor()

            try:
                # Consulta para verificar si el usuario existe con las credenciales proporcionadas
                cursor.execute("""
                    SELECT * FROM usuarios
                    WHERE email = :email AND clave = :clave
                """, {'email': email, 'clave': clave})

                # Obtén el resultado de la consulta
                usuario = cursor.fetchone()
                print("Resultado de la consulta de usuario:", usuario)  # Depuración: muestra el resultado

                if usuario:
                    session['usuario_nombre'] = usuario[1]  # Asegúrate de que el índice corresponde al nombre del usuario
                    session['usuario_rol'] = usuario[5].strip().lower()
                    flash(f'Bienvenido, {usuario[1]}!', 'success')

                   
                    # Redirigir según el rol
                    if usuario[5].strip().lower() == 'administrador':  # Compara el rol en minúsculas y sin espacios extra
                        return redirect(url_for('entidad'))  # Redirige a la página de Administradores
                    else:
                        return redirect(url_for('empleado_areas')) 
                else:
                    # Credenciales inválidas
                    flash("Correo o contraseña incorrectos", "danger")
            except oracledb.DatabaseError as e:
                print(f"Error al buscar el usuario: {e}")
            finally:
                cursor.close()
                connection.close()

        return render_template('login.html')



@app.route('/login_actual', methods=['GET', 'POST'])
def login_actual():
    if 'email' in session:  # Si ya hay una sesión activa
        flash('Ya tienes una sesión activa. Cierra la sesión actual para iniciar otra.', 'info')
        return redirect(url_for('home'))  # Redirigir al home o donde prefieras

    # Lógica de inicio de sesión (mostrada anteriormente)


## Funcion para cerrar sesion 

@app.route('/logout')
def logout():
    session.clear()  # Elimina todos los datos de la sesión
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('login'))


## Función para validar que el rol que ingresa a la gestión de áreas es el administrador y seleccionar toda la tabla de áreas en la base de datos.

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
        try:
            # Obtener la conexión usando la función definida
            connection = obtener_conexion()
            
            # Obtener el nombre del área
            nombre_area = request.form.get('nombre-area')
            
            # Obtener los valores de los checkboxes
            elementos = request.form.getlist('elementos')
            
            # Crear un diccionario para los elementos y su valor (0 o 1)
            area_data = {
                'pared': 1 if 'Pared' in elementos else 0,
                'suelo': 1 if 'Suelo' in elementos else 0,
                'puerta': 1 if 'Puerta' in elementos else 0,
                'ventana': 1 if 'Ventana' in elementos else 0,
                'escritorio': 1 if 'Escritorio' in elementos else 0,
                'mesas': 1 if 'Mesas' in elementos else 0,
                'sillas': 1 if 'Sillas' in elementos else 0,
                'sanitario': 1 if 'Sanitario' in elementos else 0,
                'lavamanos': 1 if 'Lavamanos' in elementos else 0,
                'casa': 1 if 'Casa' in elementos else 0,
                'rodadero': 1 if 'Rodadero' in elementos else 0,
                'biblioteca': 1 if 'Biblioteca' in elementos else 0,
                'piscina_pelotas': 1 if 'Piscina pelotas' in elementos else 0
            }
            
            # Realizar la inserción en la base de datos
            cursor = connection.cursor()
            query = """
            INSERT INTO area (nombre_area, pared, suelo, puerta, ventana, escritorio, mesas, sillas, 
                              sanitario, lavamanos, casa, rodadero, biblioteca, piscina_pelotas)
            VALUES (:nombre_area, :pared, :suelo, :puerta, :ventana, :escritorio, :mesas, :sillas, 
                    :sanitario, :lavamanos, :casa, :rodadero, :biblioteca, :piscina_pelotas)
            """
            
            cursor.execute(query, {
                'nombre_area': nombre_area,
                'pared': area_data['pared'],
                'suelo': area_data['suelo'],
                'puerta': area_data['puerta'],
                'ventana': area_data['ventana'],
                'escritorio': area_data['escritorio'],
                'mesas': area_data['mesas'],
                'sillas': area_data['sillas'],
                'sanitario': area_data['sanitario'],
                'lavamanos': area_data['lavamanos'],
                'casa': area_data['casa'],
                'rodadero': area_data['rodadero'],
                'biblioteca': area_data['biblioteca'],
                'piscina_pelotas': area_data['piscina_pelotas']
            })
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Confirmación en la consola
            print(f"Área '{nombre_area}' creada con éxito con los siguientes datos: {area_data}")
            # Redirigir a una página de confirmación o la página de inicio
            return redirect(url_for('gestion_area'))
        
        except oracledb.DatabaseError as e:
            error, = e.args
            print(f"Error de base de datos: {error.message}")
            return "Hubo un problema al guardar el área en la base de datos."
        
        except Exception as e:
            print(f"Ocurrió un error: {str(e)}")
            return "Hubo un problema al procesar su solicitud."
    
    # Si el método es GET, renderizar el template de creación de área
    return render_template('crear_area.html')




@app.route('/gestion_area')
def gestion_area():
    # Usar la función de conexión externa para obtener la conexión a la base de datos
    connection = obtener_conexion()
    cursor = connection.cursor()
    
    # Realizar la consulta para obtener solo los registros donde al menos un campo es igual a 1
    cursor.execute("""
        SELECT id_area, nombre_area, 
               CASE WHEN pared = 1 THEN 'Si' ELSE NULL END AS pared,
               CASE WHEN suelo = 1 THEN 'Si' ELSE NULL END AS suelo,
               CASE WHEN puerta = 1 THEN 'Si' ELSE NULL END AS puerta,
               CASE WHEN ventana = 1 THEN 'Si' ELSE NULL END AS ventana,
               CASE WHEN escritorio = 1 THEN 'Si' ELSE NULL END AS escritorio,
               CASE WHEN mesas = 1 THEN 'Si' ELSE NULL END AS mesas,
               CASE WHEN sillas = 1 THEN 'Si' ELSE NULL END AS sillas,
               CASE WHEN sanitario = 1 THEN 'Si' ELSE NULL END AS sanitario,
               CASE WHEN lavamanos = 1 THEN 'si' ELSE NULL END AS lavamanos,
               CASE WHEN casa = 1 THEN 'Si' ELSE NULL END AS casa,
               CASE WHEN rodadero = 1 THEN 'Si' ELSE NULL END AS rodadero,
               CASE WHEN biblioteca = 1 THEN 'Si' ELSE NULL END AS biblioteca,
               CASE WHEN piscina_pelotas = 1 THEN 'Si' ELSE NULL END AS piscina_pelotas
        FROM area
    """)
    
    # Obtener los nombres de las columnas y los datos de las filas
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    
    # Pasar los datos a la plantilla
    return render_template('gestion_area.html', columns=columns, rows=rows)




@app.route('/eliminar_area/<int:id_area>', methods=['POST'])
def eliminar_area(id_area):
    connection = obtener_conexion()
    cursor = connection.cursor()

    try:
        print(f"Intentando eliminar área con ID: {id_area}")

        # Primero eliminar los registros relacionados en limpieza
        cursor.execute("DELETE FROM limpieza WHERE id_area = :id_area", {'id_area': id_area})
        connection.commit()

        # Luego eliminar el área
        cursor.execute("DELETE FROM area WHERE id_area = :id_area", {'id_area': id_area})
        connection.commit()

    except Exception as e:
        print(f"Error al eliminar área: {e}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('gestion_area'))





@app.route('/areas/empleado')
def lista_areas_empleado():
    # Verifica si el usuario está logueado y es un empleado
    if 'usuario' not in session:
        return redirect(url_for('login'))  # Si no está logueado, redirige al login

    # Verifica si el usuario es un empleado
    if not es_Empleado():  # Esta función debe verificar si el rol del usuario es 'empleado'
        return redirect(url_for('entidad'))  # Si no es empleado, redirige a la entidad

    # Conexión a la base de datos para obtener las áreas
    connection = obtener_conexion()
    cursor = connection.cursor()

    cursor.execute("SELECT id_area, nombre_area FROM area")
    areas = cursor.fetchall()  # Obtén todas las áreas

    cursor.close()
    connection.close()

    # Renderiza la plantilla con las áreas
    return render_template('empleado_areas.html', areas=areas)



# Establecer el cursor para devolver diccionarios


@app.route('/editar_area/<int:id_area>', methods=['GET', 'POST'])
def editar_area(id_area):
    connection = obtener_conexion()
    cursor = connection.cursor()

    if request.method == 'POST':
        # Obtener los valores del formulario
        nombre_area = request.form['nombre_area']
        elementos = request.form.getlist('elementos')  # Lista de checkboxes seleccionados

        print(f"Datos recibidos: nombre_area={nombre_area}, elementos={elementos}")

        # Consultar los datos existentes en la base de datos
        cursor.execute("SELECT * FROM area WHERE id_area = :id_area", {'id_area': id_area})
        area = cursor.fetchone()

        if area:
            # Actualizar los valores, manteniendo los anteriores si no se seleccionan
            pared = 1 if 'Pared' in elementos else area[2]
            suelo = 1 if 'Suelo' in elementos else area[3]
            puerta = 1 if 'Puerta' in elementos else area[4]
            ventana = 1 if 'Ventana' in elementos else area[5]
            escritorio = 1 if 'Escritorio' in elementos else area[6]
            mesas = 1 if 'Mesas' in elementos else area[7]
            sillas = 1 if 'Sillas' in elementos else area[8]
            sanitario = 1 if 'Sanitario' in elementos else area[9]
            lavamanos = 1 if 'Lavamanos' in elementos else area[10]
            casa = 1 if 'Casa' in elementos else area[11]
            rodadero = 1 if 'Rodadero' in elementos else area[12]
            biblioteca = 1 if 'Biblioteca' in elementos else area[13]
            piscina_pelotas = 1 if 'Piscina pelotas' in elementos else area[14]

            # Actualizar la base de datos
            try:
                cursor.execute("""
                    UPDATE area
                    SET nombre_area = :nombre_area,
                        pared = :pared,
                        suelo = :suelo,
                        puerta = :puerta,
                        ventana = :ventana,
                        escritorio = :escritorio,
                        mesas = :mesas,
                        sillas = :sillas,
                        sanitario = :sanitario,
                        lavamanos = :lavamanos,
                        casa = :casa,
                        rodadero = :rodadero,
                        biblioteca = :biblioteca,
                        piscina_pelotas = :piscina_pelotas
                    WHERE id_area = :id_area
                """, {
                    'nombre_area': nombre_area,
                    'pared': pared,
                    'suelo': suelo,
                    'puerta': puerta,
                    'ventana': ventana,
                    'escritorio': escritorio,
                    'mesas': mesas,
                    'sillas': sillas,
                    'sanitario': sanitario,
                    'lavamanos': lavamanos,
                    'casa': casa,
                    'rodadero': rodadero,
                    'biblioteca': biblioteca,
                    'piscina_pelotas': piscina_pelotas,
                    'id_area': id_area
                })
                connection.commit()
                flash('Área actualizada correctamente', 'success')
            except oracledb.DatabaseError as e:
                connection.rollback()
                flash(f'Error al actualizar el área: {str(e)}', 'danger')
            finally:
                cursor.close()
                connection.close()

            return redirect(url_for('gestion_area'))
        else:
            flash('Área no encontrada', 'danger')
            return redirect(url_for('gestion_area'))

    else:
        cursor.execute("SELECT * FROM area WHERE id_area = :id_area", {'id_area': id_area})
        area = cursor.fetchone()

        if not area:
            flash("El área no fue encontrada.", "danger")
            return redirect(url_for('gestion_area'))

        # Filtrar los elementos seleccionados y pasarlos a la plantilla
        elementos = [
            'Pared' if area[2] else '',
            'Suelo' if area[3] else '',
            'Puerta' if area[4] else '',
            'Ventana' if area[5] else '',
            'Escritorio' if area[6] else '',
            'Mesas' if area[7] else '',
            'Sillas' if area[8] else '',
            'Sanitario' if area[9] else '',
            'Lavamanos' if area[10] else '',
            'Casa' if area[11] else '',
            'Rodadero' if area[12] else '',
            'Biblioteca' if area[13] else '',
            'Piscina pelotas' if area[14] else ''
        ]
        # Filtrar los elementos vacíos
        elementos = [e for e in elementos if e]

        cursor.close()
        connection.close()

        return render_template('editar_area.html', area=area, elementos=elementos)





### Empleado areas
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import oracledb

@app.route('/empleado/areas', methods=['GET', 'POST'])
def empleado_areas():
    connection = obtener_conexion()
    cursor = connection.cursor()

    try:
        # Obtener áreas disponibles
        query_areas = "SELECT id_area, nombre_area FROM area"
        cursor.execute(query_areas)
        areas = cursor.fetchall()
        print("Áreas obtenidas:", areas)

        # Obtener la fecha actual con formato correcto
        fecha_actual = datetime.today().strftime('%Y-%m-%d')

        # Manejo del método GET
        if request.method == 'GET':
            id_area = request.args.get('id_area')
            print("ID de área seleccionada (GET):", id_area)

            if not id_area:
                return render_template('empleado_areas.html', areas=areas, elementos={}, 
                                       usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual)

            # Consulta específica para los elementos del área
            query_elementos = """
            SELECT pared, suelo, puerta, ventana, escritorio, mesas, sillas, sanitario, lavamanos,
                   casa, rodadero, biblioteca, piscina_pelotas
            FROM area 
            WHERE id_area = :id_area
            """
            cursor.execute(query_elementos, {'id_area': int(id_area)})
            area_seleccionada = cursor.fetchone()

            elementos = {}
            if area_seleccionada:
                elementos = {
                    "pared": area_seleccionada[0],
                    "suelo": area_seleccionada[1],
                    "puerta": area_seleccionada[2],
                    "ventana": area_seleccionada[3],
                    "escritorio": area_seleccionada[4],
                    "mesas": area_seleccionada[5],
                    "sillas": area_seleccionada[6],
                    "sanitario": area_seleccionada[7],
                    "lavamanos": area_seleccionada[8],
                    "casa": area_seleccionada[9],
                    "rodadero": area_seleccionada[10],
                    "biblioteca": area_seleccionada[11],
                    "piscina_pelotas": area_seleccionada[12],
                }

            return render_template('empleado_areas.html', areas=areas, elementos=elementos, 
                                   usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual)

        # Manejo del método POST
        elif request.method == 'POST':
            id_area = request.form.get('id_area')
            print("ID de área seleccionada (POST):", id_area)

            if not id_area:
                raise ValueError("No se seleccionó un área.")

            fue_limpio = request.form.getlist('fue_limpio[]')
            observaciones = request.form.get('observaciones', '')

            print("Datos recibidos para limpieza:")
            print("Elementos limpios:", fue_limpio)
            print("Observaciones:", observaciones)

            query_insert = """
            INSERT INTO limpieza (id_area, responsable, elemento, fue_limpio, fecha, observaciones) 
            VALUES (:id_area, :responsable, :elemento, :fue_limpio, TO_DATE(:fecha, 'YYYY-MM-DD'), :observaciones)
            """
            if fue_limpio:
                for elemento in fue_limpio:
                    cursor.execute(query_insert, {
                        'id_area': int(id_area),
                        'responsable': session.get('usuario_nombre', 'Desconocido'),
                        'elemento': elemento,
                        'fue_limpio': 1,
                        'fecha': fecha_actual,  # Ya tiene el formato correcto
                        'observaciones': observaciones or '',
                    })
                connection.commit()
                print("Limpieza registrada con éxito.")
            return redirect(url_for('empleado_areas'))

    except ValueError as e:
        print("Error:", e)
        return render_template('empleado_areas.html', areas=areas, elementos={}, 
                               usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual, error=str(e))
    except oracledb.DatabaseError as e:
        print("Error de base de datos:", e)
        return render_template('empleado_areas.html', areas=areas, elementos={}, 
                               usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual, error="Error en la base de datos.")
    except Exception as e:
        print("Error al procesar la solicitud:", e)
        return render_template('empleado_areas.html', areas=areas, elementos={}, 
                               usuario_nombre=session.get('usuario_nombre'), fecha=fecha_actual, error="Ocurrió un error inesperado.")
    finally:
        cursor.close()
        connection.close()



## REPORTES LIMPIEZA 

@app.route('/reportes', methods=['GET'])
def reportes():
    connection = obtener_conexion()
    cursor = connection.cursor()

    # Obtener los parámetros de filtro del formulario
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    responsable = request.args.get('responsable')
    area = request.args.get('area')

    
    try:
        # Construir la consulta SQL dinámicamente
        query = """
            SELECT TO_CHAR(l.fecha, 'DD/MM/YYYY'), l.id_area, a.nombre_area, 
                   l.responsable, l.elemento, l.fue_limpio, l.observaciones
            FROM limpieza l
            JOIN area a ON l.id_area = a.id_area
            WHERE 1=1
        """
        filtros = {}

        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
            query += " AND l.fecha >= TO_DATE(:fecha_inicio, 'DD/MM/YYYY')"
            filtros['fecha_inicio'] = fecha_inicio

        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").strftime("%d/%m/%Y")
            query += " AND l.fecha <= TO_DATE(:fecha_fin, 'DD/MM/YYYY')"
            filtros['fecha_fin'] = fecha_fin


        if responsable:
            query += " AND LOWER(l.responsable) LIKE LOWER(:responsable)"
            filtros['responsable'] = f"%{responsable}%"

        if area:
            query += " AND LOWER(a.nombre_area) LIKE LOWER(:area)"
            filtros['area'] = f"%{area}%"

        query += " ORDER BY l.fecha"

        cursor.execute(query, filtros)
        resultados = cursor.fetchall()

        # Agrupar los datos por fecha
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



## GENERAR REPORTES EN PDF 


from datetime import datetime
from datetime import date 
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

@app.route('/generar_pdf', methods=['GET'])
def generar_pdf():
    connection = obtener_conexion()
    cursor = connection.cursor()

    try:
        # Consulta para incluir el nombre del área
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

    # Crear el PDF
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []
    
    # Agregar logo 
    
    logo_path = "app/static/images/Logo.png"  # Ruta del logo
    logo = Image(logo_path, width=100, height=50)  # Ajusta tamaño del logo
    elements.append(logo)
    header_canvas = canvas.Canvas(output, pagesize=letter)
    header_canvas.drawImage(logo_path, x=50, y=720, width=8.5 * inch, height=4.5 * inch) 

    # Agregar título
    styles = getSampleStyleSheet()
    title = Paragraph("Reporte de Limpieza", styles['Title'])
    elements.append(title)

    # Crear tabla con encabezados
    data = [
        ["Fecha", "Área", "Responsable", "Elemento", "¿Fue Limpio?", "Observaciones"]
    ]

    # Agregar los datos
    for reporte in reportes:
        data.append([
            reporte[0].strftime("%D/%M/%Y"),# Fecha
            reporte[1],                # Nombre del área
            reporte[2],                # Responsable
            reporte[3],                # Elemento
            "Sí" if reporte[4] else "No",  # ¿Fue Limpio?
            reporte[5] or ""           # Observaciones
        ])

    # Crear la tabla
    table = Table(data)

    # Aplicar estilo a la tabla
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),           # Fondo para encabezados
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),      # Color del texto de encabezados
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                  # Alinear texto al centro
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),        # Fuente para encabezados
        ('FONTSIZE', (0, 0), (-1, -1), 10),                    # Tamaño de fuente
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),                # Padding en encabezados
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),         # Fondo para datos
        ('GRID', (0, 0), (-1, -1), 1, colors.black),           # Bordes de la tabla
    ]))

    # Agregar tabla a los elementos
    elements.append(table)
    
    
    # Agregar firma parte inferior 
    
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Firma del Responsable:", styles['Normal']))
    elements.append(Spacer(1, 50))  # Espacio para la firma
    elements.append(Paragraph("_______________________", styles['Normal']))
    elements.append(Paragraph("Nombre del Responsable", styles['Normal']))

    # Construir el PDF
    doc.build(elements)
    output.seek(0)

    # Enviar el PDF como respuesta
    return Response(
        output,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=reporte_limpieza.pdf"}
    )

## GESTIÓN USUARIO


@app.route('/gestion_usuario')
def gestion_usuario():
    # Usar la función de conexión externa para obtener la conexión a la base de datos
    connection = obtener_conexion()
    cursor = connection.cursor()
    
    # Realizar la consulta para obtener solo los usuarios de la base de datos 
    cursor.execute("""
       SELECT id, nombre, apellido, email, rol FROM usuarios
    
    """)
    
    # Obtener los nombres de las columnas y los datos de las filas
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    
    # Pasar los datos a la plantilla
    return render_template('gestion_usuario.html', columns=columns, rows=rows)


@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    # Usar la función de conexión externa para obtener la conexión a la base de datos
    connection = obtener_conexion()
    cursor = connection.cursor()
    
    # Realizar la eliminación del registro con el id especificado
    cursor.execute("DELETE FROM usuarios WHERE id = :id", {'id': id})
    
    # Confirmar los cambios en la base de datos
    connection.commit()
    
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    
    # Redirigir a la página donde se visualizan los registros
    return redirect(url_for('gestion_usuario'))


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    # Lógica para obtener y actualizar al usuario
    connection = obtener_conexion()
    cursor = connection.cursor()

    if request.method == 'GET':
        # Obtener los datos del usuario por su ID
        cursor.execute("SELECT id, nombre, apellido, email, rol FROM usuarios WHERE id = :id", {'id': id})
        usuario = cursor.fetchone()

        if not usuario:
            flash("Usuario no encontrado", "danger")
            return redirect(url_for('gestion_usuario'))
        

        return render_template('editar_usuario.html', usuario=usuario)
    
        

    elif request.method == 'POST':
        # Actualizar los datos del usuario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        rol = request.form.get('rol')

        try:
            cursor.execute("""
                UPDATE usuarios
                SET nombre = :nombre, apellido = :apellido, email = :email, rol = :rol
                WHERE id = :id
            """, {'nombre': nombre, 'apellido': apellido, 'email': email, 'rol': rol, 'id': id})
            connection.commit()
            flash("Usuario actualizado correctamente", "success")
        except Exception as e:
            flash(f"Error al actualizar usuario: {e}", "danger")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('gestion_usuario'))




### APIs


  # API para crear un usuario 
  
@app.route('/api/registro', methods=['POST'])
def registro_usuario():
    # Obtener los datos del formulario en formato JSON
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    clave = data.get('clave')
    rol = data.get('rol')

    # Validar campos obligatorios
    if not nombre or not apellido or not email or not clave or not rol:
        return jsonify({"message": "Todos los campos son obligatorios."}), 400

    # Validar que el rol sea uno de los valores permitidos
    if rol not in ['Empleado', 'Administrador']:
        return jsonify({"message": "Rol inválido."}), 400

    try:
        # Usar la función obtener_conexion() para conectar a la base de datos
        connection = obtener_conexion()
        if connection is None:
            return jsonify({"message": "Error de conexión a la base de datos."}), 500

        cursor = connection.cursor()

        # Consulta SQL para insertar los datos
        query = """
        INSERT INTO usuarios (id, nombre, apellido, email, clave, rol)
        VALUES (usuarios_seq.NEXTVAL, :nombre, :apellido, :email, :clave, :rol)
        """
        
        # Ejecutar la consulta con los valores en un diccionario
        cursor.execute(query, {
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "clave": clave,
            "rol": rol
        })

        # Confirmar los cambios
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Usuario registrado con éxito."}), 200

    except Exception as e:
        print(f"Error al registrar el usuario: {e}")
        return jsonify({"message": "Hubo un problema al registrar el usuario."}), 500




# OBTENER USUARIOS 


@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        # Establecer conexión
        connection = obtener_conexion()
        if connection is None:
            raise Exception("No se pudo establecer la conexión con la base de datos.")
        
        cursor = connection.cursor()

        # Ejecutar la consulta
        cursor.execute("SELECT id, nombre, apellido, email, rol FROM usuarios")
        usuarios = cursor.fetchall()

        # Convertir los resultados en una lista de diccionarios
        usuarios_list = [
            {
                "id": usuario[0],
                "nombre": usuario[1],
                "apellido": usuario[2],
                "email": usuario[3],
                "rol": usuario[4]
            }
            for usuario in usuarios
        ]

        # Respuesta en formato JSON
        return jsonify(usuarios_list), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "No se pudieron obtener los usuarios"}), 500
    finally:
        # Cerrar cursores y conexión si están abiertos
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()




# ACTUALIZAR USUARIO 

@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    try:
        # Obtener datos del request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se enviaron datos"}), 400

        nombre = data.get('nombre')
        apellido = data.get('apellido')
        email = data.get('email')
        clave = data.get('clave')
        rol = data.get('rol')

        # Validar que los campos requeridos no estén vacíos
        if not (nombre and apellido and email and rol):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        # Conexión a la base de datos
        connection = obtener_conexion()
        if connection is None:
            raise Exception("No se pudo establecer la conexión con la base de datos.")
        
        cursor = connection.cursor()

        # Actualizar datos del usuario
        cursor.execute("""
            UPDATE usuarios
            SET nombre = :nombre, apellido = :apellido, email = :email, clave = :clave, rol = :rol
            WHERE id = :id
        """, {"nombre": nombre, "apellido": apellido, "email": email, "clave": clave, "rol": rol, "id": id})
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify({"message": "Usuario actualizado correctamente"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "No se pudo actualizar el usuario"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

        
        
# ELIMINAR USUARIO 

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario_api(id):
    try:
        # Conexión a la base de datos
        connection = obtener_conexion()
        if connection is None:
            raise Exception("No se pudo establecer la conexión con la base de datos.")
        
        cursor = connection.cursor()

        # Eliminar usuario por ID
        cursor.execute("DELETE FROM usuarios WHERE id = :id", {"id": id})
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify({"message": "Usuario eliminado correctamente"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "No se pudo eliminar el usuario"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()





if __name__ == '__main__':
    app.run(debug=True)



