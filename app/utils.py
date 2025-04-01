import oracledb
from flask import session

def obtener_conexion():
    connection = oracledb.connect(
        user="sys",
        password="123",
        dsn="localhost:1521/xe",
         mode=oracledb.SYSDBA
    )
    return connection

def es_Administrador():
    return 'rol' in session and session['rol'] == 'Administrador'

def es_Empleado():
    if 'usuario' in session:
        connection = obtener_conexion()
        cursor = connection.cursor()
        cursor.execute("SELECT rol FROM ejemplo WHERE id_usuario = :id_usuario", [session['usuario']])
        rol = cursor.fetchone()
        cursor.close()
        connection.close()

        if rol and rol[0] == 'Empleado':
            return True
    return False
