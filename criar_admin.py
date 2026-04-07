from backend.app.routes import app
from backend.app.models import db, Usuario
from werkzeug.security import generate_password_hash

def criar_primeiro_admin():
    with app.app_context():
        # Verifica se já existe um admin
        admin_existente = Usuario.query.filter_by(username='admin').first()
        
        if not admin_existente:
            # Gerar a senha criptografada
            senha_hash = generate_password_hash('123') # A senha será 123
            
            novo_admin = Usuario(
                username='admin',
                password=senha_hash,
                is_admin=True
            )
            
            db.session.add(novo_admin)
            db.session.commit()
            print("✅ Usuário ADMIN criado com sucesso!")
            print("👤 Usuário: admin")
            print("🔑 Senha: 123")
        else:
            print("⚠️ O usuário 'admin' já existe no banco de dados.")

if __name__ == "__main__":
    criar_primeiro_admin()