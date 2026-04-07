import sys
import os

# Garante que o Python encontre a pasta backend
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.app import create_app, db
from backend.app.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 1. Procura se já existe um usuário chamado 'admin'
    admin_existente = Usuario.query.filter_by(username='admin').first()
    
    if not admin_existente:
        # 2. Se NÃO existir, cria do zero com a senha '123'
        novo_admin = Usuario(
            username='admin',
            password=generate_password_hash('123'),
            is_admin=True
        )
        db.session.add(novo_admin)
        db.session.commit()
        print("✅ Primeiro acesso ADMIN criado: User: admin | Senha: 123")
    else:
        # 3. Se JÁ existir, ele não faz nada (preserva sua senha atual)
        print("ℹ️ Usuario admin ja existe. Acesso preservado.")