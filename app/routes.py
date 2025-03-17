from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .utils import obtener_conexion, es_Administrador, es_Empleado
import oracledb
from app import app

main = Blueprint('main', __name__)


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
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        clave = request.form['clave']
        rol = request.form['rol']
        
       

        # Conexión para crear usuario
        connection = obtener_conexion()
        cursor = connection.cursor()

        try:
            cursor.execute(""" 
                INSERT INTO ejemplo (nombre, apellido, email, clave, rol) 
                VALUES (:nombre, :apellido, :email, :clave, :rol)
            """, [nombre, apellido, email, clave, rol])
            connection.commit()
            
            print("Datos insertados correctamente.")
            # Redirige al login después de registro exitoso
            return redirect(url_for('login'))
            
        except oracledb.DatabaseError as e:
            print(f"Error al insertar los datos: {e}")
            connection.rollback()
            # Mostrar mensaje de error en el formulario
            return render_template('registro.html', error="Error al crear la cuenta. Por favor, inténtalo de nuevo.")
        
        finally:
            cursor.close()
            connection.close()

    # Renderiza el formulario de registro cuando se accede a la ruta con método GET
    return render_template('registro.html')


## Función para que el usuario se pueda logear o registrar uno nuevo.


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        clave = request.form['clave']

        connection = obtener_conexion()
        cursor = connection.cursor()

        try:
            # Consulta para verificar si el usuario existe con las credenciales proporcionadas
            cursor.execute("""
                SELECT * FROM ejemplo
                WHERE email = :email AND clave = :clave
            """, {'email': email, 'clave': clave})

            # Obtén el resultado de la consulta
            usuario = cursor.fetchone()
            print("Resultado de la consulta de usuario:", usuario)  # Depuración: muestra el resultado

            if usuario:
                # Credenciales válidas
                session['usuario'] = usuario[0]  # Guarda la sesión con el ID o email del usuario
                print("Sesión iniciada con el usuario:", session['usuario']) 
                return redirect(url_for('entidad'))  # Redirige a la página entidad
            else:
                # Credenciales inválidas
                flash("Correo o contraseña incorrectos", "danger")
        except oracledb.DatabaseError as e:
            print(f"Error al buscar el usuario: {e}")
        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')


## Función para validar que el rol que ingresa a la gestión de áreas es el administrador y seleccionar toda la tabla de áreas en la base de datos.

@app.route('/entidad')
def entidad():
    # Verifica si el usuario es administrador
    if not es_Administrador():
        return redirect(url_for('login'))  # si no, redirige al login 
    connection = obtener_conexion()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM area")
    areas = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('entidad_admin.html', areas=areas)





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
                'paredes': 1 if 'Paredes' in elementos else 0,
                'pisos': 1 if 'Pisos' in elementos else 0,
                'puertas': 1 if 'Puertas' in elementos else 0,
                'ventanas': 1 if 'Ventanas' in elementos else 0,
                'escritorio_profesora': 1 if 'Escritorio profesor' in elementos else 0,
                'mesas': 1 if 'Mesas' in elementos else 0,
                'sillas': 1 if 'Sillas' in elementos else 0,
                'sanitario': 1 if 'Sanitario' in elementos else 0,
                'lavamanos': 1 if 'Lavamanos' in elementos else 0,
                'casa_muñeca': 1 if 'Casa muñeca' in elementos else 0,
                'rodadero': 1 if 'Rodadero' in elementos else 0,
                'biblioteca': 1 if 'Biblioteca' in elementos else 0,
                'piscina_de_pelotas': 1 if 'Piscina pelotas' in elementos else 0
            }
            
            # Realizar la inserción en la base de datos
            cursor = connection.cursor()
            query = """
            INSERT INTO area (nombre_de_area, paredes, pisos, puertas, ventanas, escritorio_profesora, mesas, sillas, 
                              sanitario, lavamanos, casa_muñeca, rodadero, biblioteca, piscina_de_pelotas)
            VALUES (:nombre_area, :paredes, :pisos, :puertas, :ventanas, :escritorio_profesora, :mesas, :sillas, 
                    :sanitario, :lavamanos, :casa_muñeca, :rodadero, :biblioteca, :piscina_de_pelotas)
            """
            
            cursor.execute(query, {
                'nombre_area': nombre_area,
                'paredes': area_data['paredes'],
                'pisos': area_data['pisos'],
                'puertas': area_data['puertas'],
                'ventanas': area_data['ventanas'],
                'escritorio_profesora': area_data['escritorio_profesora'],
                'mesas': area_data['mesas'],
                'sillas': area_data['sillas'],
                'sanitario': area_data['sanitario'],
                'lavamanos': area_data['lavamanos'],
                'casa_muñeca': area_data['casa_muñeca'],
                'rodadero': area_data['rodadero'],
                'biblioteca': area_data['biblioteca'],
                'piscina_de_pelotas': area_data['piscina_de_pelotas']
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
       SELECT * FROM area
    WHERE paredes = 1 OR pisos = 1 OR puertas = 1 OR ventanas = 1
    OR escritorio_profesora = 1 OR mesas = 1 OR sillas = 1 OR sanitario = 1
    OR lavamanos = 1 OR casa_muñeca = 1 OR rodadero = 1 OR biblioteca = 1
    OR piscina_de_pelotas = 1
    """)
    
    # Obtener los nombres de las columnas y los datos de las filas
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    
    # Pasar los datos a la plantilla
    return render_template('gestion_area.html', columns=columns, rows=rows)


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


@app.route('/formulario/limpieza/<int:id_area>')
def formulario_limpieza(id_area):
    # Obtener el área por ID
    connection = obtener_conexion()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM area WHERE id_area = :id_area", [id_area])
    area = cursor.fetchone()
    
    cursor.close()
    connection.close()

    # Renderiza el formulario de limpieza para el área seleccionada
    return render_template('formulario_limpieza.html', area=area)



@app.route('/editar_area/<int:id_area>', methods=['GET', 'POST'])
def editar_area(id_area):
    connection = obtener_conexion()
    cursor = connection.cursor()

    if request.method == 'POST':
        # Obtener datos del formulario
        paredes = int(request.form['paredes'])
        pisos = int(request.form['pisos'])
        puertas = int(request.form['puertas'])
        ventanas = int(request.form['ventanas'])
        escritorio_profesora = int(request.form['escritorio_profesora'])
        mesas = int(request.form['mesas'])
        sillas = int(request.form['sillas'])
        sanitario = int(request.form['sanitario'])
        lavamanos = int(request.form['lavamanos'])
        casa_muñeca = int(request.form['casa_muñeca'])
        rodadero = int(request.form['rodadero'])
        biblioteca = int(request.form['biblioteca'])
        piscina_de_pelotas = int(request.form['piscina_de_pelotas'])

        # Actualizar el registro
        cursor.execute("""
            UPDATE area
            SET paredes = :paredes, pisos = :pisos, puertas = :puertas, ventanas = :ventanas,
                escritorio_profesora = :escritorio_profesora, mesas = :mesas, sillas = :sillas,
                sanitario = :sanitario, lavamanos = :lavamanos, casa_muñeca = :casa_muñeca,
                rodadero = :rodadero, biblioteca = :biblioteca, piscina_de_pelotas = :piscina_de_pelotas
            WHERE id = :id
        """, {
            'paredes': paredes, 'pisos': pisos, 'puertas': puertas, 'ventanas': ventanas,
            'escritorio_profesora': escritorio_profesora, 'mesas': mesas, 'sillas': sillas,
            'sanitario': sanitario, 'lavamanos': lavamanos, 'casa_muñeca': casa_muñeca,
            'rodadero': rodadero, 'biblioteca': biblioteca, 'piscina_de_pelotas': piscina_de_pelotas,
            'id': id
        })
        connection.commit()

        return redirect(url_for('gestion_area'))

    # Obtener los datos del registro para mostrar en el formulario
    cursor.execute("SELECT * FROM area WHERE id_area = :id_area", {'id_area': id_area})
    registro = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('editar_area.html', registro=registro)


@app.route('/eliminar_area/<int:id_area>', methods=['POST'])
def eliminar_area(id_area):
    # Usar la función de conexión externa para obtener la conexión a la base de datos
    connection = obtener_conexion()
    cursor = connection.cursor()
    
    # Realizar la eliminación del registro con el id especificado
    cursor.execute("DELETE FROM area WHERE id_area = :id_area", {'id_area': id_area})
    
    # Confirmar los cambios en la base de datos
    connection.commit()
    
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    
    # Redirigir a la página donde se visualizan los registros
    return redirect(url_for('gestion_area'))





