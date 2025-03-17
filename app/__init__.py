from flask import Flask
from .config import Config
from .routes import main
from .utils import obtener_conexion

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.register_blueprint(main)  # Registro de blueprint para rutas

    return app
