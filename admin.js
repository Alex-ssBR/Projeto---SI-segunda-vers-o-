// --- INICIALIZAÇÃO ---
async function carregarAdmin() {
    const resAuth = await fetch('/api/check_login');
    const user = await resAuth.json();
    
    if (!user.logged_in || !user.is_admin) {
        window.location.href = "/home";
        return;
    }
    
    document.getElementById('adm-name').innerText = user.username;
    renderAll();
}

function renderAll() {
    renderDashboard();
    renderEquipe();
    renderManutencao();
}

// --- NAVEGAÇÃO ---
function showSection(id, btn) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
    renderAll();
}

// --- DASHBOARD: Estatísticas e Logs (Limite de 20) ---
async function renderDashboard() {
    try {
        // 1. Busca as contagens (Stats) de uma vez só
        const resStats = await fetch('/api/admin/stats');
        const stats = await resStats.json();

        if (resStats.ok) {
            document.getElementById('stat-abertos').innerText = stats.abertos || 0;
            document.getElementById('stat-fechados').innerText = stats.fechados || 0;
            document.getElementById('stat-pats').innerText = stats.patrimonios || 0;
        }

        // 2. Busca os Logs
        const resLogs = await fetch('/api/admin/logs');
        const logs = await resLogs.json();
        const tbody = document.querySelector('#tabela-logs tbody');
        
        if (logs.length === 0) {
            tbody.innerHTML = "<tr><td colspan='3' style='text-align:center'>Nenhuma atividade recente.</td></tr>";
        } else {
            tbody.innerHTML = logs.map(l => `
                <tr>
                    <td>${l.data}</td>
                    <td><strong>${l.user || 'Sistema'}</strong></td>
                    <td>${l.acao}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error("Erro ao carregar Dashboard:", error);
    }
}

// --- EQUIPE: Gerenciar Técnicos ---
async function renderEquipe() {
    const res = await fetch('/api/admin/users');
    const users = await res.json();
    const tbody = document.querySelector('#tabela-users tbody');
    
    tbody.innerHTML = users.map(u => `
        <tr>
            <td>${u.id}</td>
            <td><strong>${u.username}</strong></td>
            <td>${u.is_admin ? '<span style="color:var(--primary)">Admin</span>' : 'Técnico'}</td>
            <td>
                ${u.username !== 'admin' ? `<button class="btn btn-danger btn-sm" onclick="deletarUsuario(${u.id})"><i class="fas fa-trash"></i> Excluir</button>` : '<em>Protegido</em>'}
            </td>
        </tr>
    `).join('');
}

async function addNewUser() {
    const userField = document.getElementById('addUsername');
    const passField = document.getElementById('addPassword');

    if (!userField.value || !passField.value) {
        alert("Preencha usuário e senha!");
        return;
    }

    const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: userField.value,
            password: passField.value,
            is_admin: false
        })
    });

    if (res.ok) {
        alert("✅ Técnico cadastrado com sucesso!");
        userField.value = "";
        passField.value = "";
        closeModal('modalUser');
        renderEquipe();
    } else {
        const data = await res.json();
        alert("❌ Erro: " + data.message);
    }
}

async function deletarUsuario(id) {
    if (!confirm("🚨 Deseja realmente excluir este técnico? Isso afetará os logs antigos.")) return;

    try {
        const res = await fetch(`/api/admin/users/${id}`, { method: 'DELETE' });
        const data = await res.json();

        if (res.ok) {
            alert("✅ Usuário removido!");
            renderEquipe();
            renderDashboard();
        } else {
            alert("❌ Erro: " + data.message);
        }
    } catch (e) {
        alert("❌ Erro de conexão ao tentar excluir.");
    }
}

// --- MANUTENÇÃO: Patrimônios e Exclusão em Cascata ---
async function renderManutencao() {
    const res = await fetch('/api/patrimonios');
    const pats = await res.json();
    const filtro = document.getElementById('filtroPat').value.toUpperCase();
    const tbody = document.querySelector('#tabela-pats tbody');
    
    tbody.innerHTML = pats.filter(p => p.numero.includes(filtro)).map(p => `
        <tr>
            <td><strong>${p.numero}</strong></td>
            <td>${p.qtd_casos} chamados</td>
            <td style="display: flex; gap: 10px;">
                <button class="btn btn-blue btn-sm" onclick="verCasosAdmin(${p.id}, '${p.numero}')"><i class="fas fa-search"></i> Ver Casos</button>
                <button class="btn btn-danger btn-sm" onclick="deletarPatrimonio(${p.id}, '${p.numero}')"><i class="fas fa-trash"></i> Apagar Tudo</button>
            </td>
        </tr>
    `).join('');
}

async function deletarPatrimonio(id, numero) {
    if (!confirm(`🚨 PERIGO: Deseja apagar o patrimônio ${numero}?\n\nIsso apagará permanentemente todos os chamados e conversas deste equipamento!`)) return;

    const res = await fetch(`/api/admin/patrimonios/${id}`, { method: 'DELETE' });
    if (res.ok) {
        alert("✅ Patrimônio e históricos removidos!");
        renderAll();
    } else {
        alert("Erro ao excluir patrimônio.");
    }
}

// --- CASOS E TICKETS ---
async function verCasosAdmin(patId, numero) {
    document.getElementById('modalCasosTitulo').innerText = `Casos: ${numero}`;
    const res = await fetch(`/api/casos/${patId}`);
    const casos = await res.json();
    const tbody = document.querySelector('#tabela-casos-admin tbody');
    
    tbody.innerHTML = casos.map(c => `
        <tr>
            <td>#${c.id}</td>
            <td>${c.solicitante}</td>
            <td>${c.status.toUpperCase()}</td>
            <td>${c.problema}</td>
            <td style="display: flex; gap: 5px;">
                <button class="btn btn-blue btn-sm" onclick="verTicketsAdmin(${c.id})"><i class="fas fa-comments"></i></button>
                <button class="btn btn-danger btn-sm" onclick="deletarCaso(${c.id}, ${patId}, '${numero}')"><i class="fas fa-trash"></i></button>
            </td>
        </tr>
    `).join('');
    openModal('modalCasos');
}

async function deletarCaso(id, patId, numero) {
    if (!confirm(`Deseja apagar apenas o chamado #${id}?`)) return;

    const res = await fetch(`/api/admin/casos/${id}`, { method: 'DELETE' });
    if (res.ok) {
        alert("✅ Chamado removido!");
        verCasosAdmin(patId, numero);
        renderDashboard();
    } else {
        alert("Erro ao excluir chamado.");
    }
}

async function verTicketsAdmin(casoId) {
    const res = await fetch(`/api/tickets/${casoId}`);
    const tickets = await res.json();
    const div = document.getElementById('chat-tickets-admin');
    div.innerHTML = tickets.map(t => `
        <div class="ticket-box">
            <small><strong>${t.autor}</strong> - ${t.data}</small>
            <p>${t.msg}</p>
        </div>
    `).join('');
    openModal('modalTickets');
}

// --- AUXILIARES ---
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

carregarAdmin();