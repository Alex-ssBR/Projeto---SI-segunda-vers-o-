let userLogado = null;
let patAtivo = null;
let casoAtivo = null;

async function inicializar() {
    // 1. Checar Login
    const res = await fetch('/api/check_login');
    const data = await res.json();
    
    if (!data.logged_in) {
        window.location.href = "/";
        return;
    }

    userLogado = data;
    document.getElementById('sessaoUsuario').innerText = data.username;

    if (data.is_admin) {
        const btnAdmin = document.getElementById('btnIrParaAdmin');
        if (btnAdmin) btnAdmin.style.display = 'flex';
    }

    // 2. Carregar Dados
    renderPatrimonios();
    renderAvisos();
}

// --- PATRIMÔNIOS ---
async function renderPatrimonios(filtro = "") {
    const grid = document.getElementById('gridPatrimonios');
    const res = await fetch('/api/patrimonios');
    const pats = await res.json();
    
    grid.innerHTML = pats.filter(p => p.numero.includes(filtro.toUpperCase())).map(p => `
        <div class="card-patrimonio" onclick="abrirModalCasos(${p.id}, '${p.numero}')">
            <i class="fas fa-desktop"></i>
            <h3>${p.numero}</h3>
            <small>${p.qtd_casos} chamados registrados</small>
        </div>
    `).join('');
}

// --- CASOS ---
async function abrirModalCasos(id, numero) {
    patAtivo = {id, numero};
    document.getElementById('tituloPatrimonio').innerText = `Casos do Patrimônio: ${numero}`;
    
    const res = await fetch(`/api/casos/${id}`);
    const casos = await res.json();
    
    const tbody = document.getElementById('corpoTabelaCasos');
    tbody.innerHTML = casos.map(c => `
        <tr>
            <td>#${c.id}</td>
            <td>${c.solicitante}</td>
            <td><span class="status-badge status-${c.status}">${c.status.toUpperCase()}</span></td>
            <td><button class="btn btn-search" onclick="abrirTickets(${c.id})">Tickets</button></td>
        </tr>
    `).join('');
    document.getElementById('modalListaCasos').style.display = 'flex';
}

// --- TICKETS / CHAT ---
async function abrirTickets(id) {
    const resDet = await fetch(`/api/admin/casos_detalhes/${id}`);
    const c = await resDet.json();
    casoAtivo = c;

    document.getElementById('tituloCasoTickets').innerText = `Histórico Chamado #${id}`;
    document.getElementById('infoCaso').innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <p><strong>Solicitante:</strong> ${c.solicitante}</p>
            <p><strong>Patrimônio:</strong> ${c.patrimonio}</p>
            <p><strong>Setor:</strong> ${c.secretaria || '-'}</p>
            <p><strong>Ramal:</strong> ${c.ramal || '-'}</p>
        </div>
        <p style="margin-top:10px"><strong>Problema:</strong> ${c.problema}</p>
    `;

    const resTks = await fetch(`/api/tickets/${id}`);
    const tickets = await resTks.json();
    
    const area = document.getElementById('ticketArea');
    area.innerHTML = tickets.map(t => `
        <div class="ticket ${t.autor === userLogado.username ? 'me' : 'other'}">
            <span class="ticket-meta">${t.autor} - ${t.data}</span>
            <p>${t.msg}</p>
        </div>
    `).join('');
    
    const isFechado = c.status === 'fechado';
    document.getElementById('areaInteracao').style.display = isFechado ? 'none' : 'flex';
    document.getElementById('areaImpressao').style.display = isFechado ? 'flex' : 'none';
    
    document.getElementById('modalTickets').style.display = 'flex';
    area.scrollTop = area.scrollHeight;
}

// --- AÇÕES ---

// Submissão do Formulário com Trava de Segurança (Requisito solicitado)
document.getElementById('formNovoCaso').onsubmit = async (e) => {
    e.preventDefault();
    const dados = {
        patrimonio: document.getElementById('formPat').value,
        solicitante: document.getElementById('formNome').value,
        secretaria: document.getElementById('formSec').value,
        departamento: document.getElementById('formDepto').value,
        ramal: document.getElementById('formRamal').value,
        problema: document.getElementById('formProb').value
    };
    
    const res = await fetch('/api/casos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(dados)
    });
    
    const resultado = await res.json();

    if (res.ok) {
        alert("✅ Chamado aberto com sucesso!");
        fecharModal('modalCriarCaso');
        renderPatrimonios();
    } else {
        // Exibe o erro enviado pelo Python (Ex: Patrimônio já tem chamado aberto)
        alert("⚠️ ATENÇÃO: " + (resultado.message || "Erro ao abrir chamado."));
    }
};

document.getElementById('btnEnviarTicket').onclick = async () => {
    const msg = document.getElementById('inputTicket').value;
    if (!msg) return;
    
    await fetch(`/api/tickets/${casoAtivo.id}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mensagem: msg })
    });
    
    document.getElementById('inputTicket').value = "";
    abrirTickets(casoAtivo.id);
};

document.getElementById('btnFinalizarCaso').onclick = async () => {
    if(!confirm("Encerrar chamado?")) return;
    await fetch(`/api/casos/${casoAtivo.id}/fechar`, { method: 'POST' });
    fecharModal('modalTickets');
    abrirModalCasos(patAtivo.id, patAtivo.numero);
};

function imprimirChamado() {
    if (casoAtivo && casoAtivo.id) {
        window.open(`/imprimir/${casoAtivo.id}`, '_blank');
    } else {
        alert("Erro: Nenhum caso selecionado.");
    }
}

// --- AVISOS ---
async function renderAvisos() {
    const res = await fetch('/api/avisos');
    const avisos = await res.json();
    const container = document.getElementById('avisos-container');
    
    container.innerHTML = avisos.map(a => `
        <div class="mensagem-aviso">
            <p>${a.msg}</p>
            <span class="aviso-meta">
                <i class="fas fa-user"></i> ${a.autor} | 
                <i class="fas fa-clock"></i> ${a.data}
            </span>
        </div>
    `).join('');
}

document.getElementById('btnEnviarAviso').onclick = async () => {
    const msg = document.getElementById('campoAviso').value;
    if(!msg) return;
    await fetch('/api/avisos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mensagem: msg })
    });
    document.getElementById('campoAviso').value = "";
    renderAvisos();
};

// --- AUXILIARES ---
function fecharModal(id) { document.getElementById(id).style.display = 'none'; }
function abrirModalCriar() { document.getElementById('modalCriarCaso').style.display = 'flex'; }
function abrirNovoCasoPeloPatrimonio() {
    abrirModalCriar();
    document.getElementById('formPat').value = patAtivo.numero;
}

document.getElementById('btnSair').onclick = () => window.location.href = "/api/logout";
document.getElementById('btnBuscar').onclick = () => renderPatrimonios(document.getElementById('campoBusca').value);



inicializar();