from flask import Blueprint, render_template, request, jsonify, redirect, url_for, make_response, render_template_string
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import db, Usuario, Patrimonio, Caso, Ticket, Aviso, Log
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

# --- FUNÇÃO AUXILIAR DE LOGS ---
def logar(acao):
    try:
        if current_user.is_authenticated:
            novo_log = Log(usuario_id=current_user.id, acao=acao)
            db.session.add(novo_log)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar log: {e}")

# --- ROTAS DE PÁGINAS ---
@main.route('/')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.home_page'))
    return render_template('login.html')

@main.route('/home')
@login_required
def home_page():
    return render_template('home.html')

@main.route('/admin')
@login_required
def admin_page():
    if not current_user.is_admin: return "Acesso Negado", 403
    return render_template('admin.html')

# --- APIs DE AUTENTICAÇÃO ---
@main.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = Usuario.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password, data.get('password')):
        login_user(user)
        logar("Realizou login no sistema")
        return jsonify({"success": True, "is_admin": user.is_admin, "username": user.username})
    return jsonify({"success": False, "message": "Usuário ou senha inválidos"}), 401

@main.route('/api/check_login')
def check_login():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "username": current_user.username, "is_admin": current_user.is_admin})
    return jsonify({"logged_in": False})

@main.route('/api/logout')
def logout():
    logar("Saiu do sistema")
    logout_user()
    return redirect(url_for('main.login_page'))

# --- APIs DO ADMINISTRADOR (EQUIPE, LOGS E STATS) ---

@main.route('/api/admin/stats')
@login_required
def get_stats():
    if not current_user.is_admin: return jsonify({"error": "Negado"}), 403
    abertos = Caso.query.filter_by(status='aberto').count()
    fechados = Caso.query.filter_by(status='fechado').count()
    total_pats = Patrimonio.query.count()
    return jsonify({"abertos": abertos, "fechados": fechados, "patrimonios": total_pats})

@main.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin: return jsonify({"error": "Negado"}), 403
    if request.method == 'POST':
        data = request.json
        if Usuario.query.filter_by(username=data['username']).first():
            return jsonify({"success": False, "message": "Usuário já existe"}), 400
        hash_p = generate_password_hash(data['password'])
        u = Usuario(username=data['username'], password=hash_p, is_admin=False)
        db.session.add(u); db.session.commit()
        logar(f"Criou técnico: {data['username']}")
        return jsonify({"success": True})
    users = Usuario.query.all()
    return jsonify([{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in users])

@main.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def deletar_usuario(user_id):
    if not current_user.is_admin: return jsonify({"error": "Negado"}), 403
    u = Usuario.query.get(user_id)
    if u and u.username != 'admin':
        nome = u.username
        Log.query.filter_by(usuario_id=user_id).update({Log.usuario_id: None})
        Ticket.query.filter_by(usuario_id=user_id).update({Ticket.usuario_id: None})
        Aviso.query.filter_by(usuario_id=user_id).update({Aviso.usuario_id: None})
        db.session.delete(u); db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@main.route('/api/admin/logs')
@login_required
def get_logs():
    if not current_user.is_admin: return jsonify({"error": "Negado"}), 403
    logs = Log.query.order_by(Log.data_criacao.desc()).limit(20).all()
    return jsonify([{"data": l.data_criacao.strftime('%d/%m %H:%M'), "user": l.usuario.username if l.usuario else "Sistema", "acao": l.acao} for l in logs])

# --- APIs DE PATRIMÔNIOS E CASOS ---

@main.route('/api/patrimonios')
@login_required
def get_pats():
    pats = Patrimonio.query.all()
    return jsonify([{"id": p.id, "numero": p.numero, "qtd_casos": len(p.casos)} for p in pats])

@main.route('/api/casos', methods=['POST'])
@login_required
def criar_caso():
    data = request.json
    num_patrimonio = data['patrimonio']

    # 1. Verifica se o patrimônio já existe no banco
    pat = Patrimonio.query.filter_by(numero=num_patrimonio).first()
    
    if pat:
        # 2. CONDIÇÃO ESPECIAL: Busca se existe algum caso ABERTO para este patrimônio
        caso_aberto = Caso.query.filter_by(patrimonio_id=pat.id, status='aberto').first()
        
        if caso_aberto:
            # Se encontrou um caso aberto, retorna erro e impede a criação
            return jsonify({
                "success": False, 
                "message": f"Não é possível abrir: O patrimônio {num_patrimonio} já possui o chamado #{caso_aberto.id} em aberto!"
            }), 400

    # 3. Se não existir o patrimônio, cria ele agora
    if not pat:
        pat = Patrimonio(numero=num_patrimonio)
        db.session.add(pat)
        db.session.flush() # Gera o ID para usar abaixo
    
    # 4. Se chegou aqui, é porque o patrimônio não tem casos abertos. Pode criar o novo.
    novo = Caso(
        patrimonio_id=pat.id, 
        solicitante=data['solicitante'],
        secretaria=data.get('secretaria'), 
        departamento=data.get('departamento'),
        ramal=data.get('ramal'), 
        problema=data['problema']
    )
    
    db.session.add(novo)
    db.session.commit()
    logar(f"Abriu chamado #{novo.id} (Pat: {num_patrimonio})")
    
    return jsonify({"success": True})
@main.route('/api/casos/<int:pat_id>')
@login_required
def listar_casos(pat_id):
    casos = Caso.query.filter_by(patrimonio_id=pat_id).all()
    return jsonify([{"id": c.id, "solicitante": c.solicitante, "status": c.status, "problema": c.problema} for c in casos])

@main.route('/api/admin/casos_detalhes/<int:caso_id>')
@login_required
def detalhes_caso(caso_id):
    c = Caso.query.get(caso_id)
    if not c: return jsonify({"error": "Não encontrado"}), 404
    return jsonify({
        "id": c.id, "patrimonio": c.patrimonio.numero, "solicitante": c.solicitante,
        "secretaria": c.secretaria or "N/A", "departamento": c.departamento or "N/A",
        "ramal": c.ramal or "N/A", "problema": c.problema, "status": c.status,
        "data": c.data_criacao.strftime('%d/%m/%Y %H:%M')
    })

# --- ROTAS DE EXCLUSÃO ---

@main.route('/api/admin/patrimonios/<int:pat_id>', methods=['DELETE'])
@login_required
def deletar_patrimonio(pat_id):
    if not current_user.is_admin: return jsonify({"error": "Negado"}), 403
    p = Patrimonio.query.get(pat_id)
    if p:
        numero = p.numero
        db.session.delete(p); db.session.commit()
        logar(f"Excluiu patrimônio: {numero}")
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@main.route('/api/admin/casos/<int:caso_id>', methods=['DELETE'])
@login_required
def deletar_caso(caso_id):
    if not current_user.is_admin: return jsonify({"error": "Negado"}), 403
    c = Caso.query.get(caso_id)
    if c:
        db.session.delete(c); db.session.commit()
        logar(f"Excluiu chamado #{caso_id}")
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

# --- IMPRESSÃO (CORRIGIDA E LIMPA) ---

@main.route('/imprimir/<int:caso_id>')
@login_required
def imprimir_relatorio(caso_id):
    c = Caso.query.get(caso_id)
    if not c: return "Erro: Caso não encontrado", 404
    
    tks = Ticket.query.filter_by(caso_id=caso_id).all()
    
    # Monta histórico apenas com o texto puro (sem datas ou nomes)
    historico_texto = ""
    for t in tks:
        historico_texto += f"<div class='msg-item'>{t.mensagem}</div>"

    logo_url = url_for('static', filename='img/logo_santaisabel (longo).png')

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 0mm; }}
            body {{ font-family: 'Segoe UI', sans-serif; padding: 15mm; color: #000; line-height: 1.4; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }}
            .header img {{ width: 100%; max-height: 100px; object-fit: contain; }}
            .title {{ font-size: 18px; font-weight: bold; text-transform: uppercase; margin-top: 10px; text-align: center; }}
            .section-title {{ background: #f2f2f2; padding: 6px 10px; font-weight: bold; border: 1px solid #000; margin-top: 15px; text-transform: uppercase; font-size: 13px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #000; border-top: none; padding: 10px; gap: 8px; }}
            .label {{ font-weight: bold; font-size: 10px; text-transform: uppercase; color: #555; display: block; }}
            .box {{ border: 1px solid #000; border-top: none; padding: 12px; font-size: 14px; min-height: 50px; background: #fff; }}
            .msg-item {{ margin-bottom: 5px; padding-bottom: 3px; border-bottom: 1px solid #eee; }}
            .signature-area {{ margin-top: 70px; display: flex; justify-content: space-between; }}
            .sig-box {{ border-top: 1px solid #000; width: 45%; text-align: center; padding-top: 5px; font-size: 11px; font-weight: bold; }}
            @media print {{ .no-print {{ display: none; }} }}
            .btn-p {{ background: #2563eb; color: #fff; padding: 10px; border: none; border-radius: 4px; cursor: pointer; float: right; }}
        </style>
    </head>
    <body>
        <button class="no-print btn-p" onclick="window.print()">CONFIRMAR IMPRESSÃO</button>
        <div class="header">
            <img src="{logo_url}">
            <div class="title">Relatório de Atendimento Técnico - #{c.id}</div>
        </div>
        <div class="section-title">Informações Gerais</div>
        <div class="info-grid">
            <div><span class="label">Solicitante:</span> {c.solicitante}</div>
            <div><span class="label">Patrimônio:</span> {c.patrimonio.numero}</div>
            <div><span class="label">Secretaria:</span> {c.secretaria or '---'}</div>
            <div><span class="label">Setor:</span> {c.departamento or '---'}</div>
            <div><span class="label">Abertura:</span> {c.data_criacao.strftime('%d/%m/%Y %H:%M')}</div>
            <div><span class="label">Status:</span> <strong>{c.status.upper()}</strong></div>
        </div>
        <div class="section-title">Descrição do Problema</div>
        <div class="box">{c.problema}</div>
        <div class="section-title">Histórico de Soluções e Notas</div>
        <div class="box">{historico_texto}</div>
        <div class="signature-area">
            <div class="sig-box">Responsável Técnico</div>
            <div class="sig-box">Assinatura do Solicitante</div>
        </div>
        <div style="text-align: center; font-size: 9px; color: #888; margin-top: 30px;">
            Gerado pelo Sistema SI em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

# --- APIs DE TICKETS, AVISOS E FECHAMENTO ---

@main.route('/api/tickets/<int:caso_id>', methods=['GET', 'POST'])
@login_required
def tickets(caso_id):
    if request.method == 'POST':
        tk = Ticket(caso_id=caso_id, usuario_id=current_user.id, mensagem=request.json['mensagem'])
        db.session.add(tk); db.session.commit()
        return jsonify({"success": True})
    tks = Ticket.query.filter_by(caso_id=caso_id).all()
    return jsonify([{"autor": t.usuario.username, "msg": t.mensagem, "data": t.data_criacao.strftime('%d/%m/%Y %H:%M')} for t in tks])

@main.route('/api/casos/<int:caso_id>/fechar', methods=['POST'])
@login_required
def fechar_caso(caso_id):
    c = Caso.query.get(caso_id)
    if c:
        c.status = 'fechado'
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@main.route('/api/avisos', methods=['GET', 'POST'])
@login_required
def avisos():
    if request.method == 'POST':
        av = Aviso(usuario_id=current_user.id, mensagem=request.json['mensagem'])
        db.session.add(av); db.session.commit()
        return jsonify({"success": True})
    limite = datetime.utcnow() - timedelta(days=2)
    avs = Aviso.query.filter(Aviso.data_criacao > limite).order_by(Aviso.data_criacao.desc()).all()
    return jsonify([{"autor": a.usuario.username, "msg": a.mensagem, "data": a.data_criacao.strftime('%d/%m %H:%M')} for a in avs])