#!/usr/bin/env python3
"""
Banco Digital Grana Fácil - Treinamento AulasHack
AVISO: Contém vulnerabilidades intencionais para fins educacionais
"""

from flask import Flask, request, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from seed import run_seed
import base64
import socket
import subprocess
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "banco_digital.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de Usuário
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id            = db.Column(db.Integer,     primary_key=True)
    username      = db.Column(db.String(80),  unique=True,  nullable=False)
    password      = db.Column(db.String(120),               nullable=False)
    # Campos adicionados para compatibilidade com o app mobile
    cpf           = db.Column(db.String(14),  unique=True,  nullable=True)
    pin           = db.Column(db.String(6),                 nullable=True)
    nome_completo = db.Column(db.String(120),               nullable=True)
    email         = db.Column(db.String(120), unique=True,  nullable=True)
    saldo         = db.Column(db.Float,       default=0.0,  nullable=True)
    cartao_ativo  = db.Column(db.Boolean,     default=True, nullable=True)
    chave_pix     = db.Column(db.String(14),                nullable=True)
    limite_diario = db.Column(db.Float,       default=500.0,nullable=True)
    conta_ativa   = db.Column(db.Boolean,     default=True, nullable=True)

    def __repr__(self):
        return f'<Usuario {self.username}>'


class Transacao(db.Model):
    __tablename__    = 'transacoes'
    id               = db.Column(db.Integer, primary_key=True)
    conta_origem_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    conta_destino_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    valor            = db.Column(db.Float,   nullable=False)
    tipo             = db.Column(db.String(20), nullable=False)   # 'pix' | 'transferencia'
    descricao        = db.Column(db.String(200))
    data             = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Transacao {self.id} R${self.valor}>'

# Funções auxiliares
def obter_ip_local():
    """Obtém o IP da rede local"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def gerar_token_reset(password):
    rot13 = ''
    for char in password:
        if char.isalpha():
            if char.islower():
                rot13 += chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
            else:
                rot13 += chr((ord(char) - ord('A') + 13) % 26 + ord('A'))
        else:
            rot13 += char
    token = base64.b64encode(rot13.encode()).decode()
    return token

def decodificar_token_reset(token):
    try:
        rot13 = base64.b64decode(token).decode()
        password = ''
        for char in rot13:
            if char.isalpha():
                if char.islower():
                    password += chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
                else:
                    password += chr((ord(char) - ord('A') + 13) % 26 + ord('A'))
            else:
                password += char
        return password
    except:
        return None

# Template HTML da página de login
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Banco Digital Grana Fácil - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            position: relative;
        }
        .header {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            background-color: rgba(255, 255, 255, 0.95);
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            display: flex;
            align-items: center;
        }
        .logo-icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 20px;
        }
        .container {
            background-color: white;
            padding: 50px 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 420px;
            margin-top: 80px;
        }
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 14px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.3s;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .reset-link {
            text-align: center;
            margin-top: 20px;
        }
        .reset-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .reset-link a:hover {
            text-decoration: underline;
        }
        .message {
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
        }
        .error {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef5350;
        }
        .success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #66bb6a;
        }
        .support-button {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s;
            z-index: 1000;
        }
        .support-button:hover {
            transform: scale(1.1);
        }
        .support-button-icon {
            color: white;
            font-size: 28px;
        }
        .support-modal {
            display: none;
            position: fixed;
            bottom: 110px;
            right: 30px;
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            width: 350px;
            z-index: 1001;
        }
        .support-modal.active {
            display: block;
        }
        .support-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px 15px 0 0;
            font-weight: 600;
        }
        .support-body {
            padding: 20px;
        }
        .support-body textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            resize: vertical;
            font-family: inherit;
            font-size: 14px;
        }
        .support-body textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .support-body button {
            margin-top: 15px;
        }
        .support-response {
            margin-top: 15px;
            padding: 12px;
            background-color: #f5f5f5;
            border-radius: 8px;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
        }
        .footer {
            position: fixed;
            bottom: 10px;
            left: 0;
            right: 0;
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            font-weight: 500;
            z-index: 999;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon">💰</div>
            Banco Digital Grana Fácil
        </div>
    </div>

    <div class="container">
        <h2>Bem-vindo</h2>
        <p class="subtitle">Acesse sua conta com segurança</p>
        
        {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
        {% endif %}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Usuário</label>
                <input type="text" id="username" name="username" required placeholder="Digite seu usuário">
            </div>
            
            <div class="form-group">
                <label for="password">Senha</label>
                <input type="password" id="password" name="password" required placeholder="Digite sua senha">
            </div>
            
            <button type="submit">Entrar na Conta</button>
        </form>
        
        <div class="reset-link">
            <a href="/reset">Esqueci minha senha</a>
        </div>
    </div>

    <div class="support-button" onclick="toggleSupport()">
        <div class="support-button-icon">💬</div>
    </div>

    <div class="support-modal" id="supportModal">
        <div class="support-header">
            Suporte Técnico
        </div>
        <div class="support-body">
            <textarea id="supportMessage" rows="4" placeholder="Digite sua mensagem ou comando de diagnóstico..."></textarea>
            <button onclick="sendSupport()">Enviar</button>
            <div id="supportResponse" class="support-response" style="display:none;"></div>
        </div>
    </div>

    <script>
        function toggleSupport() {
            const modal = document.getElementById('supportModal');
            modal.classList.toggle('active');
        }

        function sendSupport() {
            const message = document.getElementById('supportMessage').value;
            const responseDiv = document.getElementById('supportResponse');
            
            fetch('/support', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                responseDiv.style.display = 'block';
                responseDiv.textContent = data.response || 'Resposta do servidor';
            })
            .catch(error => {
                responseDiv.style.display = 'block';
                responseDiv.textContent = 'Erro ao processar solicitação';
            });
        }
    </script>
    <div class="footer">
        Powered by <strong>AulasHack</strong>
    </div>
</body>
</html>
"""

# Template da página de reset de senha
RESET_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Banco Digital Grana Fácil - Reset de Senha</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .header {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            background-color: rgba(255, 255, 255, 0.95);
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            display: flex;
            align-items: center;
        }
        .logo-icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 20px;
        }
        .container {
            background-color: white;
            padding: 50px 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 450px;
            margin-top: 80px;
        }
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 14px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.3s;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .back-link a:hover {
            text-decoration: underline;
        }
        .message {
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
        }
        .error {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef5350;
        }
        .success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #66bb6a;
        }
        .info {
            background-color: #e3f2fd;
            color: #1565c0;
            border: 1px solid #42a5f5;
        }
        .token-display {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 15px 0;
            border: 2px solid #667eea;
        }
        .challenge-box {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #667eea;
        }
        .challenge-box h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 18px;
        }
        .challenge-box p {
            color: #555;
            font-size: 14px;
            line-height: 1.6;
        }
        .footer {
            position: fixed;
            bottom: 10px;
            left: 0;
            right: 0;
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            font-weight: 500;
            z-index: 999;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon">💰</div>
            Banco Digital Grana Fácil
        </div>
    </div>

    <div class="container">
        <h2>Recuperação de Senha</h2>
        <p class="subtitle">Siga as instruções para recuperar seu acesso</p>
        
        {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
        {% endif %}
        
        {% if not token %}
        <form method="POST" action="/reset">
            <div class="form-group">
                <label for="username">Digite seu usuário</label>
                <input type="text" id="username" name="username" required placeholder="seu.usuario">
            </div>
            
            <button type="submit">Solicitar Token de Recuperação</button>
        </form>
        {% else %}
        <div class="message info">
            Token de recuperação gerado com sucesso!
        </div>
        
        <div class="challenge-box">
            <h3>🔐 Desafio de Segurança</h3>
            <p>Seu token contém uma informação oculta. Decodifique o token abaixo e descubra o valor secreto para confirmar sua identidade.</p>
        </div>
        
        <div class="token-display">
            {{ token }}
        </div>
        
        <form method="POST" action="/reset-confirm">
            <input type="hidden" name="token" value="{{ token }}">
            <input type="hidden" name="username" value="{{ username }}">
            
            <div class="form-group">
                <label for="secret_value">Digite o valor oculto no token</label>
                <input type="text" id="secret_value" name="secret_value" required placeholder="Decodifique o token">
            </div>
            
            <button type="submit">Verificar e Resetar Senha</button>
        </form>
        {% endif %}
        
        <div class="back-link">
            <a href="/">← Voltar ao Login</a>
        </div>
    </div>
    <div class="footer">
        Powered by <strong>AulasHack</strong>
    </div>
</body>
</html>
"""

# Página de sucesso após login
SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Banco Digital Grana Fácil - Área do Cliente</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .header {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            background-color: rgba(255, 255, 255, 0.95);
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            display: flex;
            align-items: center;
        }
        .logo-icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 20px;
        }
        .container {
            background-color: white;
            padding: 60px 50px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            margin-top: 80px;
        }
        .success-icon {
            font-size: 80px;
            margin-bottom: 20px;
            color: #4CAF50;
        }
        h1 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 32px;
        }
        .username {
            color: #333;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            font-size: 16px;
            margin-bottom: 30px;
        }
        a {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        a:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon">💰</div>
            Banco Digital Grana Fácil
        </div>
    </div>

    <div class="container">
        <div class="success-icon">✓</div>
        <h1>Acesso Autorizado!</h1>
        <p class="username">Bem-vindo(a), {{ username }}!</p>
        <p>Você acessou sua conta com sucesso.</p>
        <a href="/">Sair</a>
    </div>
</body>
</html>
"""

SECRET_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Painel Administrativo</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background-color: #0a0a0a;
            color: #00ff00;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #1a1a1a;
            padding: 40px;
            border-radius: 10px;
            border: 2px solid #00ff00;
            max-width: 700px;
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.3);
        }
        h1 {
            text-align: center;
            color: #00ff00;
            margin-bottom: 30px;
            text-shadow: 0 0 10px #00ff00;
        }
        .secret-content {
            background-color: #000;
            padding: 25px;
            border-radius: 5px;
            margin-top: 20px;
            border: 1px solid #00ff00;
        }
        pre {
            margin: 0;
            line-height: 1.6;
        }
        .warning {
            color: #ff0000;
            text-align: center;
            margin-top: 30px;
            font-weight: bold;
            text-shadow: 0 0 10px #ff0000;
        }
        .blink {
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔓 PAINEL ADMINISTRATIVO</h1>
        <p>Acesso ao painel de controle detectado.</p>
        
        <div class="secret-content">
            <h3>📄 Arquivo: database_credentials.txt</h3>
            <pre>
=========================================
  CREDENCIAIS DO SISTEMA - CONFIDENCIAL
=========================================

Servidor Principal:
  IP: 192.168.100.50
  Usuário: sysadmin
  Senha: Admin@2024!Secure

Banco de Dados MySQL:
  Host: db.granafacil.internal
  Porta: 3306
  Database: production_db
  Usuário: db_admin
  Senha: MyS3cr3tP@ssDB!2024

API Externa:
  Endpoint: https://api.granafacil.com.br
  API Key: gf_live_sk_48f9a2b1c3d5e6f7890abcdef
  Secret: 9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d

VPN Corporativa:
  Server: vpn.granafacil.corp
  Username: admin.vpn
  Password: VPN$ecur3!2024

Última atualização: 2024-11-20
=========================================
            </pre>
        </div>
        
        <div class="warning">
            <span class="blink">⚠️</span> DOCUMENTO CONFIDENCIAL - ACESSO RESTRITO <span class="blink">⚠️</span>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Página inicial com formulário de login"""
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def login():
    """Login com SQLi e enumeração de usuários"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    try:
        query = f"SELECT * FROM usuarios WHERE username = '{username}' AND password = '{password}'"
        result = db.session.execute(db.text(query))
        user = result.fetchone()
        
        if user:
            return render_template_string(SUCCESS_PAGE, username=username)
        else:
            user_check = Usuario.query.filter_by(username=username).first()
            if user_check:
                return render_template_string(LOGIN_PAGE, 
                                            message="Usuário ou senha incorretos!", 
                                            message_type="error")
            else:
                return render_template_string(LOGIN_PAGE, 
                                            message="Usuário ou senha incorretos", 
                                            message_type="error")
    except Exception as e:
        error_msg = str(e)
        return render_template_string(LOGIN_PAGE, 
                                    message=f"Erro no sistema: {error_msg}", 
                                    message_type="error")

@app.route('/support', methods=['POST'])
def support():
    """Suporte com Command Injection"""
    data = request.get_json()
    message = data.get('message', '')
    
    try:
        if message:
            result = subprocess.check_output(message, shell=True, stderr=subprocess.STDOUT, timeout=5)
            output = result.decode('utf-8', errors='ignore')
            return jsonify({'response': output})
        else:
            return jsonify({'response': 'Nenhuma mensagem recebida'})
    except subprocess.TimeoutExpired:
        return jsonify({'response': 'Comando demorou muito para executar'})
    except Exception as e:
        return jsonify({'response': f'Erro: {str(e)}'})

@app.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        return render_template_string(RESET_PAGE)
    
    username = request.form.get('username', '')
    user = Usuario.query.filter_by(username=username).first()
    
    if user:
        token = gerar_token_reset(user.password)
        return render_template_string(RESET_PAGE, 
                                    token=token,
                                    username=username,
                                    message="Token gerado com sucesso!",
                                    message_type="success")
    else:
        return render_template_string(RESET_PAGE,
                                    message="Usuário não encontrado.",
                                    message_type="error")

@app.route('/reset-confirm', methods=['POST'])
def reset_confirm():
    token = request.form.get('token', '')
    username = request.form.get('username', '')
    secret_value = request.form.get('secret_value', '')
    
    decoded_password = decodificar_token_reset(token)
    
    user = Usuario.query.filter_by(username=username).first()
    
    if user and decoded_password and secret_value == decoded_password:
        user.password = 'novaSenha123'
        db.session.commit()
        return render_template_string(LOGIN_PAGE,
                                    message=f"Parabéns! Senha resetada para: novaSenha123",
                                    message_type="success")
    else:
        return render_template_string(RESET_PAGE,
                                    message="Valor incorreto.",
                                    message_type="error")

@app.route('/admin1')
def secret_panel():
    return render_template_string(SECRET_PAGE)

@app.route('/robots.txt')
def robots():
    return "User-agent: *\nAllow: /", 200, {'Content-Type': 'text/plain'}

def init_db():
    """
    Inicializa o banco de dados.
    Se o banco já existir com usuários, mantém os dados.
    Caso contrário, chama o seed.py para criá-lo e populá-lo completamente,
    garantindo compatibilidade com a aplicação web e com o app mobile Android.
    """
    import os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banco_digital.db')

    if os.path.exists(db_path):
        # Banco já existe — apenas garante que as tabelas estão mapeadas
        with app.app_context():
            db.create_all()
        print("[+] Banco de dados existente carregado")
    else:
        # Banco não existe — executa o seed completo
        print("[*] Banco não encontrado. Executando seed...")
        run_seed()
        # Agora conecta o SQLAlchemy ao banco recém-criado
        with app.app_context():
            db.create_all()
        print("[+] Banco inicializado e populado com sucesso")

if __name__ == '__main__':
    # Inicializa o banco
    init_db()
    
    # Obtém IPs
    ip_local = obter_ip_local()
    
    print("\n" + "="*70)
    print("  BANCO DIGITAL GRANA FÁCIL - PENTEST WEB AULASHACK")
    print("="*70)
    print(f"\n[+] Servidor rodando em:")
    print(f"    - Local: http://127.0.0.1:5000")
    print(f"    - Rede:  http://{ip_local}:5000")
    print(f"[+] Banco: banco_digital.db")
    print("="*70 + "\n")
    
    # Roda em todas as interfaces
    app.run(host='0.0.0.0', port=5000, debug=False)
