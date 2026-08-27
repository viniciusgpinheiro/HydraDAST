from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from models import db, User, Booth, Message, FileUpload, Transfer
from datetime import datetime
from functools import wraps
import os
import socket

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///siga_em_frente.db'
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-nao-mude'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_COOKIE_HTTPONLY'] = False

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Função para obter IP local
def get_local_ip():
    """
    Detecta automaticamente o IP local da máquina.
    Tenta vários métodos para garantir o resultado correto.
    """
    try:
        # Método 1: Conectar a um servidor externo (sem realmente enviar dados)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Método 2: Usar gethostbyname
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip != '127.0.0.1':
                return ip
        except Exception:
            pass
    
    # Fallback: retornar localhost
    return '127.0.0.1'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        # CORRIGIDO: Usar db.session.get() em vez de User.query.get()
        user = db.session.get(User, session['user_id'])
        if user and user.role == 'admin':
            return redirect(url_for('admin_dashboard', id=101))
        elif user:
            return redirect(url_for('operator_dashboard', id=user.id))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard', id=101))
            else:
                return redirect(url_for('operator_dashboard', id=user.id))
        else:
            return render_template('login.html', error='Usuário ou senha inválidos')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard/operator', methods=['GET'])
@login_required
def operator_dashboard():
    # VULNERABILIDADE: IDOR - Não valida se o usuário pode acessar este ID
    operator_id = request.args.get('id', type=int)
    
    if operator_id is None:
        return redirect(url_for('login'))
    
    # CORRIGIDO: Usar db.session.get() em vez de User.query.get()
    operator = db.session.get(User, operator_id)
    
    if not operator or operator.role != 'operator':
        return "Operador não encontrado", 404
    
    booth = Booth.query.filter_by(booth_number=operator.booth_id).first()
    
    # Buscar mensagens para este operador (sem validação)
    messages = Message.query.filter_by(recipient_id=operator_id).all()
    
    return render_template('operator_dashboard.html', operator=operator, booth=booth, messages=messages)

@app.route('/dashboard/admin', methods=['GET'])
@login_required
def admin_dashboard():
    # VULNERABILIDADE: IDOR + PRIVILEGE ESCALATION
    # Operador consegue acessar dashboard de admin apenas alterando ?id=101
    admin_id = request.args.get('id', type=int)
    
    if admin_id != 101:
        return "ID inválido", 404
    
    # VULNERABILIDADE: Não valida privilégio ANTES de renderizar
    # Comentado para demonstração educacional de Privilege Escalation
    #user = db.session.get(User, session['user_id'])
    #if not user or user.role != 'admin':
    #    return "Acesso negado", 403
    
    # Calcular totais
    booths = Booth.query.all()
    total_vehicles = sum(b.total_vehicles for b in booths)
    total_cash = sum(b.total_cash for b in booths)
    
    # Buscar todos os operadores
    operators = User.query.filter_by(role='operator').all()
    
    return render_template('admin_dashboard.html', booths=booths, total_vehicles=total_vehicles, 
                         total_cash=total_cash, operators=operators)

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    operator_id = request.args.get('id', type=int)
    
    if operator_id is None:
        return redirect(url_for('login'))
    
    # CORRIGIDO: Usar db.session.get() em vez de User.query.get()
    operator = db.session.get(User, operator_id)
    
    if not operator or operator.role != 'operator':
        return "Operador não encontrado", 404
    
    booth = Booth.query.filter_by(booth_number=operator.booth_id).first()
    max_transfer = booth.total_cash * 0.6
    
    if request.method == 'POST':
        # VULNERABILIDADE: CSRF - Sem token CSRF
        amount = float(request.form.get('amount', 0))
        destination_booth_id = int(request.form.get('destination_booth', 0))
        
        if amount > 0 and amount <= max_transfer:
            # Realizar transferência
            # CORRIGIDO: Usar db.session.get() em vez de Booth.query.get()
            destination_booth = db.session.get(Booth, destination_booth_id)
            
            if destination_booth:
                booth.total_cash -= amount
                destination_booth.total_cash += amount
                
                transfer_record = Transfer(
                    operator_id=operator_id,
                    source_booth=booth.id,
                    destination_booth=destination_booth_id,
                    amount=amount
                )
                
                db.session.add(transfer_record)
                db.session.commit()
                
                return render_template('transfer_success.html', booth=booth, destination_booth=destination_booth, amount=amount)
        
        return render_template('transfer.html', operator=operator, booth=booth, max_transfer=max_transfer, 
                             booths=Booth.query.all(), error='Valor inválido')
    
    return render_template('transfer.html', operator=operator, booth=booth, max_transfer=max_transfer, 
                         booths=Booth.query.all())

@app.route('/message', methods=['POST'])
@login_required
def send_message():
    # CORRIGIDO: Usar db.session.get() em vez de User.query.get()
    user = db.session.get(User, session['user_id'])
    
    # VULNERABILIDADE: PRIVILEGE ESCALATION - Não valida privilégio
    # Operador consegue enviar mensagem como admin se acessar via dashboard admin
    #if user.role != 'admin':
    #    return jsonify({'error': 'Acesso negado'}), 403
    
    recipient_id = int(request.form.get('recipient_id'))
    content = request.form.get('content')
    
    # VULNERABILIDADE: XSS Armazenado - Sem sanitização do conteúdo
    message = Message(
        sender_id=user.id,
        recipient_id=recipient_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': 'Mensagem enviada'})

@app.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    # CORRIGIDO: Usar db.session.get() em vez de User.query.get()
    user = db.session.get(User, session['user_id'])
    
    # VULNERABILIDADE: Verificação fraca - Apenas checa extensão no cliente
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('files.html', error='Nenhum arquivo selecionado'), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('files.html', error='Nenhum arquivo selecionado'), 400
        
        # VULNERABILIDADE: Não valida a extensão corretamente (apenas salvando)
        filename = file.filename
        
        # Salvar arquivo sem validação de segurança
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Registrar no banco de dados
        file_upload = FileUpload(
            filename=filename,
            uploader_id=user.id
        )
        
        db.session.add(file_upload)
        db.session.commit()
        
        return render_template('files.html', success='Upload realizado com sucesso')
    
    return render_template('files.html')

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/csrf-test')
def csrf_test():
    """Endpoint para demonstração de CSRF - Página maliciosa servida do mesmo domínio"""
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Promoção de Perfume Premium!</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .container { background: white; border-radius: 20px; padding: 40px; max-width: 500px; text-align: center; }
            h1 { color: #333; margin-bottom: 20px; }
            .button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                     border: none; padding: 15px 40px; border-radius: 50px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌹 Promoção de Perfume Premium!</h1>
            <p>Clique para ganhar 10.000 pontos de fidelidade</p>
            <button class="button" onclick="submit_csrf()">💝 Ganhe Pontos Agora! 💝</button>
        </div>
        
        <form id="csrf_form" action="/transfer?id=6" method="POST" style="display:none;">
            <input type="hidden" name="amount" value="2000">
            <input type="hidden" name="destination_booth" value="1">
        </form>
        
        <script>
            function submit_csrf() {
                document.getElementById('csrf_form').submit();
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/messages/<int:operator_id>')
@login_required
def get_messages(operator_id):
    # VULNERABILIDADE: IDOR - Não valida acesso
    messages = Message.query.filter_by(recipient_id=operator_id).all()
    return jsonify([{
        'id': m.id,
        'sender': m.sender.full_name,
        'content': m.content,  # XSS: Sem escape HTML
        'timestamp': m.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    } for m in messages])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Detectar IP local
    local_ip = get_local_ip()
    
    # Exibir informações de acesso
    print("\n" + "="*80)
    print("🎓 MÁQUINA SIGA EM FRENTE - AULASHACK")
    print("="*80)
    print()
    print("✅ Aplicação iniciada com sucesso!")
    print()
    print("📍 URLS DE ACESSO:")
    print()
    print(f"  🖥️  Localhost:      http://127.0.0.1:5001")
    print(f"  🌐 Rede Local:      http://{local_ip}:5001")
    print()
    print("="*80)
    print()
    print("💡 Dicas:")
    print("  • Use a primeira URL (localhost) para testar localmente")
    print("  • Use a segunda URL para acessar de outra máquina na rede")
    print("  • Para VMs Linux na mesma rede, use: http://<IP_ACIMA>:5001")
    print()
    print("=" * 80)
    print()
    
    # Executar Flask
    app.run(debug=False, host='0.0.0.0', port=5001)