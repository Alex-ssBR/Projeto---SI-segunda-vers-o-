from flask import Flask, request, jsonify, session
from flask_mysql_connector import MySQL
from flask_cors import CORS
from datetime import datetime, timedelta
import schedule
import time
import threading
import os
from werkzeug.security import generate_password_hash, check_password_hash # Para senhas seguras
from functools import wraps
from config import Config

app = Flask(__name__)

# Configurações do Flask
app.config.from_object(Config)

# Configuração do MySQL
mysql = MySQL(app)

# Configuração do CORS para permitir requisições do frontend
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}}) # Ajuste origins para o seu domínio em produção

# --- Funções de Ajuda e Decoradores ---

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return jsonify({"message": "Não autorizado. Faça login para acessar este recurso."}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Autenticação ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # ATENÇÃO: Em um sistema real, você buscaria o usuário no banco de dados e verificaria a senha criptografada.
    # Este é um exemplo simplificado com credenciais fixas (como no seu JS).
    # Em produção, você faria algo como:
    # user = get_user_from_db(username)
    # if user and check_password_hash(user.password_hash, password):
    if username == app.config['VALID_USERNAME'] and password == app.config['VALID_PASSWORD']:
        session['logged_in'] = True
        session['username'] = username # Pode armazenar mais informações do usuário aqui
        return jsonify({"message": "Login realizado com sucesso!", "username": username}), 200
    else:
        return jsonify({"message": "Usuário ou senha inválidos."}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return jsonify({"message": "Logout realizado com sucesso."}), 200

@app.route('/api/check_login', methods=['GET'])
def check_login():
    if 'logged_in' in session and session['logged_in']:
        return jsonify({"logged_in": True, "username": session['username']}), 200
    else:
        return jsonify({"logged_in": False}), 200

# --- Rotas para Casos ---

@app.route('/api/casos', methods=['POST'])
@login_required
def criar_caso():
    data = request.get_json()
    nome_solicitante = data.get('nome')
    ramal = data.get('ramal')
    secretaria = data.get('secretaria')
    departamento = data.get('departamento')
    numero_patrimonio = data.get('patrimonio')
    problema_descricao = data.get('problema')
    solucao_descricao = data.get('solucao')
    status = data.get('status', 'aberto') # Padrão para 'aberto'

    if not nome_solicitante:
        return jsonify({"message": "O campo 'nome' é obrigatório."}), 400
    if not numero_patrimonio:
        return jsonify({"message": "O campo 'Nº Patrimônio' é obrigatório."}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO casos (nome_solicitante, ramal, secretaria, departamento, numero_patrimonio, problema_descricao, solucao_descricao, status, ultima_atualizacao) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (nome_solicitante, ramal, secretaria, departamento, numero_patrimonio, problema_descricao, solucao_descricao, status, datetime.now())
        )
        mysql.connection.commit()
        return jsonify({"message": "Caso registrado com sucesso!", "id": cur.lastrowid}), 201
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erro ao criar caso: {str(e)}"}), 500
    finally:
        cur.close()

@app.route('/api/casos', methods=['GET'])
@login_required
def listar_casos():
    cur = mysql.connection.cursor()
    termo_busca = request.args.get('busca')
    status_filtro = request.args.get('status') # Ex: 'aberto', 'fechado'
    secretaria_filtro = request.args.get('secretaria')
    departamento_filtro = request.args.get('departamento')
    
    query = "SELECT id_caso, nome_solicitante, ramal, secretaria, departamento, numero_patrimonio, problema_descricao, solucao_descricao, status, ultima_atualizacao FROM casos WHERE 1=1"
    params = []

    if termo_busca:
        query += " AND (numero_patrimonio LIKE %s OR nome_solicitante LIKE %s OR problema_descricao LIKE %s)"
        params.extend([f"%{termo_busca}%", f"%{termo_busca}%", f"%{termo_busca}%"])
    if status_filtro:
        query += " AND status = %s"
        params.append(status_filtro)
    if secretaria_filtro:
        query += " AND secretaria LIKE %s"
        params.append(f"%{secretaria_filtro}%")
    if departamento_filtro:
        query += " AND departamento LIKE %s"
        params.append(f"%{departamento_filtro}%")

    query += " ORDER BY ultima_atualizacao DESC" # Ordena do mais recente para o mais antigo

    try:
        cur.execute(query, params)
        casos = cur.fetchall()
        
        casos_formatados = []
        for caso in casos:
            casos_formatados.append({
                "id": caso[0],
                "nome": caso[1],
                "ramal": caso[2],
                "secretaria": caso[3],
                "departamento": caso[4],
                "patrimonio": caso[5],
                "problema": caso[6],
                "solucao": caso[7],
                "status": caso[8],
                "ultimaAtualizacao": caso[9].isoformat() if caso[9] else None
            })
        return jsonify(casos_formatados), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao listar casos: {str(e)}"}), 500
    finally:
        cur.close()

@app.route('/api/casos/<int:caso_id>', methods=['GET'])
@login_required
def obter_caso(caso_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT id_caso, nome_solicitante, ramal, secretaria, departamento, numero_patrimonio, problema_descricao, solucao_descricao, status, ultima_atualizacao FROM casos WHERE id_caso = %s",
            (caso_id,)
        )
        caso = cur.fetchone()
        if caso:
            caso_formatado = {
                "id": caso[0],
                "nome": caso[1],
                "ramal": caso[2],
                "secretaria": caso[3],
                "departamento": caso[4],
                "patrimonio": caso[5],
                "problema": caso[6],
                "solucao": caso[7],
                "status": caso[8],
                "ultimaAtualizacao": caso[9].isoformat() if caso[9] else None
            }
            return jsonify(caso_formatado), 200
        else:
            return jsonify({"message": "Caso não encontrado."}), 404
    except Exception as e:
        return jsonify({"message": f"Erro ao obter caso: {str(e)}"}), 500
    finally:
        cur.close()

@app.route('/api/casos/<int:caso_id>', methods=['PUT'])
@login_required
def atualizar_caso(caso_id):
    data = request.get_json()
    nome_solicitante = data.get('nome')
    ramal = data.get('ramal')
    secretaria = data.get('secretaria')
    departamento = data.get('departamento')
    numero_patrimonio = data.get('patrimonio')
    problema_descricao = data.get('problema')
    solucao_descricao = data.get('solucao')
    status = data.get('status')

    if not nome_solicitante or not numero_patrimonio or not status:
        return jsonify({"message": "Campos 'nome', 'patrimonio' e 'status' são obrigatórios."}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "UPDATE casos SET nome_solicitante=%s, ramal=%s, secretaria=%s, departamento=%s, numero_patrimonio=%s, problema_descricao=%s, solucao_descricao=%s, status=%s, ultima_atualizacao=%s WHERE id_caso=%s",
            (nome_solicitante, ramal, secretaria, departamento, numero_patrimonio, problema_descricao, solucao_descricao, status, datetime.now(), caso_id)
        )
        mysql.connection.commit()
        if cur.rowcount > 0:
            return jsonify({"message": f"Caso {caso_id} atualizado com sucesso!"}), 200
        else:
            return jsonify({"message": "Caso não encontrado ou nenhum dado alterado."}), 404
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erro ao atualizar caso: {str(e)}"}), 500
    finally:
        cur.close()

@app.route('/api/casos/<int:caso_id>/reabrir', methods=['PUT'])
@login_required
def reabrir_caso(caso_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "UPDATE casos SET status='aberto', ultima_atualizacao=%s WHERE id_caso=%s",
            (datetime.now(), caso_id)
        )
        mysql.connection.commit()
        if cur.rowcount > 0:
            return jsonify({"message": f"Caso {caso_id} reaberto com sucesso!"}), 200
        else:
            return jsonify({"message": "Caso não encontrado ou já está aberto."}), 404
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erro ao reabrir caso: {str(e)}"}), 500
    finally:
        cur.close()

@app.route('/api/casos/<int:caso_id>/download', methods=['GET'])
@login_required
def download_caso(caso_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT id_caso, nome_solicitante, ramal, secretaria, departamento, numero_patrimonio, problema_descricao, solucao_descricao, status, ultima_atualizacao FROM casos WHERE id_caso = %s",
            (caso_id,)
        )
        caso = cur.fetchone()
        if caso:
            case_details = f"""
Detalhes do Caso {caso[0]}
---------------------------
Nome: {caso[1]}
Ramal: {caso[2] or 'N/A'}
Secretaria: {caso[3] or 'N/A'}
Departamento: {caso[4] or 'N/A'}
Nº Patrimônio: {caso[5] or 'N/A'}
Problema: {caso[6] or 'N/A'}
Solução: {caso[7] or 'N/A'}
Status: {caso[8].upper()}
Última Atualização: {caso[9].strftime('%Y-%m-%d %H:%M:%S')}
            """
            # Em um sistema real, você geraria um PDF aqui.
            # Por enquanto, retornaremos como texto puro para simular o download.
            response = app.make_response(case_details)
            response.headers["Content-Disposition"] = f"attachment; filename=caso_{caso_id}.txt"
            response.headers["Content-Type"] = "text/plain"
            return response, 200
        else:
            return jsonify({"message": "Caso não encontrado para download."}), 404
    except Exception as e:
        return jsonify({"message": f"Erro ao preparar download: {str(e)}"}), 500
    finally:
        cur.close()

# --- Rotas para Avisos (Chat Lateral) ---

@app.route('/api/avisos', methods=['POST'])
@login_required
def criar_aviso():
    data = request.get_json()
    mensagem = data.get('message')

    if not mensagem:
        return jsonify({"message": "A mensagem do aviso é obrigatória."}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO avisos (mensagem, timestamp_aviso) VALUES (%s, %s)",
            (mensagem, datetime.now())
        )
        mysql.connection.commit()
        return jsonify({"message": "Aviso enviado com sucesso!", "id": cur.lastrowid}), 201
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"message": f"Erro ao enviar aviso: {str(e)}"}), 500
    finally:
        cur.close()

@app.route('/api/avisos', methods=['GET'])
@login_required
def listar_avisos():
    cur = mysql.connection.cursor()
    # Filtra avisos que expiraram (2 dias)
    two_days_ago = datetime.now() - timedelta(days=2)
    
    try:
        cur.execute(
            "SELECT id_aviso, mensagem, timestamp_aviso FROM avisos WHERE timestamp_aviso > %s ORDER BY timestamp_aviso ASC",
            (two_days_ago,)
        )
        avisos = cur.fetchall()
        
        avisos_formatados = []
        for aviso in avisos:
            avisos_formatados.append({
                "id": aviso[0],
                "message": aviso[1],
                "timestamp": aviso[2].isoformat() if aviso[2] else None
            })
        return jsonify(avisos_formatados), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao listar avisos: {str(e)}"}), 500
    finally:
        cur.close()

# --- Tarefa Agendada para Limpeza de Avisos Expirados ---

def limpar_avisos_expirados():
    with app.app_context():
        cur = mysql.connection.cursor()
        two_days_ago = datetime.now() - timedelta(days=2)
        try:
            cur.execute("DELETE FROM avisos WHERE timestamp_aviso <= %s", (two_days_ago,))
            mysql.connection.commit()
            print(f"Limpeza de avisos expirados concluída. {cur.rowcount} avisos removidos.")
        except Exception as e:
            mysql.connection.rollback()
            print(f"Erro ao limpar avisos expirados: {str(e)}")
        finally:
            cur.close()

# Agendamento da tarefa
# schedule.every(1).hour.do(limpar_avisos_expirados) # A cada hora, por exemplo
# Para testes, você pode agendar a cada 1 minuto
schedule.every(1).minute.do(limpar_avisos_expirados)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciar o scheduler em uma thread separada
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

# --- Execução do Aplicativo ---

if __name__ == '__main__':
    # Inicialização do banco de dados (opcional, para garantir que as tabelas existam ao iniciar o app)
    # Em produção, você faria isso com migrations.
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS casos (
                id_caso INTEGER PRIMARY KEY AUTO_INCREMENT, 
                nome_solicitante VARCHAR(255) NOT NULL,
                ramal VARCHAR(20),
                secretaria VARCHAR(255),
                departamento VARCHAR(255),
                numero_patrimonio VARCHAR(50) NOT NULL,
                problema_descricao TEXT,
                solucao_descricao TEXT,
                status VARCHAR(20) NOT NULL, -- 'aberto' ou 'fechado'
                ultima_atualizacao DATETIME NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS avisos (
                id_aviso INTEGER PRIMARY KEY AUTO_INCREMENT, 
                mensagem TEXT NOT NULL,
                timestamp_aviso DATETIME NOT NULL
            );
        """)
        mysql.connection.commit()
        print("Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        mysql.connection.rollback()
        print(f"Erro ao inicializar tabelas: {str(e)}")
    finally:
        cur.close()

    app.run(debug=True, host='0.0.0.0', port=5000)