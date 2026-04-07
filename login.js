document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const err = document.getElementById("errorMessage");
        
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    username: document.getElementById("username").value, 
                    password: document.getElementById("password").value 
                })
            });

            const data = await res.json();

            if (res.ok) {
                // REDIRECIONAMENTO INTELIGENTE
                if (data.is_admin === true) {
                    window.location.replace("/admin");
                } else {
                    window.location.replace("/home");
                }
            } else {
                err.textContent = data.message || "Usuário ou senha inválidos";
                err.classList.add("show");
            }
        } catch (error) {
            err.textContent = "Erro ao conectar com o servidor.";
            err.classList.add("show");
        }
    });
});