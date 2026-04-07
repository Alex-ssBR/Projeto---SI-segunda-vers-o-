import sys
import os

# Garante que o Python encontre a pasta backend
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.app import create_app

# Criamos a instância da aplicação
app = create_app()

if __name__ == '__main__':
    print("🚀 Servidor SI iniciado com sucesso!")
    print("📍 Local: http://localhost:5000")
    # 0.0.0.0 permite acesso pelo IP da sua máquina na rede local
    app.run(host='0.0.0.0', port=5000, debug=True)