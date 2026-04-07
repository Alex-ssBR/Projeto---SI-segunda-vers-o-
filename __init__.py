from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
from backend.config import Config

# Inicializamos as extensões fora da factory
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login_page'

def create_app(config_class=Config):
    app = Flask(__name__,
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    
    app.config.from_object(config_class)

    # Inicializar extensões no app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    CORS(app, supports_credentials=True)

    with app.app_context():
        # Importamos as rotas e registramos o Blueprint
        from .routes import main
        app.register_blueprint(main)
        
        # Importamos os modelos e criamos as tabelas
        from . import models
        db.create_all()

    # Configurar o carregamento do usuário para o LoginManager
    from .models import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    return app