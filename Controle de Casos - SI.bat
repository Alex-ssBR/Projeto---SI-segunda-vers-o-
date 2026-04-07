@echo off
:: Garante que o script rode na pasta onde ele está localizado
cd /d "%~dp0"

:: 1. Ativa o ambiente virtual
call venv\Scripts\activate.bat

:: 2. Sincroniza o Banco de Dados (opcional, pode remover se já estiver pronto)
python reset_admin.py

:: 3. Abre o navegador
start http://localhost:5000

:: 4. Inicia o servidor Python
:: Removi o 'pause' para não travar o script na memória
python run.py