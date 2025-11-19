import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURAÇÃO DE AMBIENTE E SEGURANÇA ---
app = Flask(__name__)
# Chave de segurança para assinar os cookies
app.secret_key = 'tony_sports_key_secure_2025_final'

# CONFIGURAÇÕES DE SEGURANÇA
app.config['SESSION_COOKIE_HTTPONLY'] = True 
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 

# CONFIGURAÇÃO DE ARMAZENAMENTO DE IMAGENS PERSISTENTE NO RENDER
# O Render precisa montar o disco neste EXATO caminho:
PERSISTENT_UPLOAD_PATH = '/var/data/tonysports_uploads'
app.config['UPLOAD_FOLDER'] = PERSISTENT_UPLOAD_PATH
# A URL base para as imagens deve ser '/uploads/'
IMAGE_URL_BASE = '/uploads/'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# Cria a pasta de uploads persistente (se não existir, o Render cria no deploy)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- CONFIGURAÇÃO DE BANCO DE DADOS ---
# Tenta usar a URL de conexão do PostgreSQL (DATABASE_URL)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Corrige a sintaxe para o SQLAlchemy (postgres:// -> postgresql://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Se não houver DATABASE_URL, usa o SQLite local para desenvolvimento
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'tony.db')

db = SQLAlchemy(app)

# A senha real é: Pristony22@
ADMIN_HASH = generate_password_hash('Pristony22@')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# --- MIDDLEWARE DE SEGURANÇA (HEADERS) ---
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

# --- ROTA PARA SERVIR IMAGENS DO DISCO PERSISTENTE (NOVA ROTA) ---
@app.route(f'{IMAGE_URL_BASE.rstrip("/")}/<filename>')
def uploaded_file(filename):
    # Usa send_from_directory para servir arquivos do disco persistente
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def index():
    category_filter = request.args.get('category')
    if category_filter:
        products = Product.query.filter_by(category=category_filter).all()
    else:
        products = Product.query.all()
    return render_template('index.html', products=products, active_cat=category_filter)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(ADMIN_HASH, password):
            session['admin'] = True
            session.modified = True
            return redirect(url_for('admin'))
        else:
            flash('Senha ou acesso negado.', 'error')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            # SALVA NO DISCO PERSISTENTE MONTADO:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            new_prod = Product(name=request.form['name'], category=request.form['category'], price=float(request.form['price']), image=filename)
            db.session.add(new_prod)
            db.session.commit()
            flash('Produto salvo com sucesso!', 'success')
            
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin.html', products=products)

@app.route('/delete/<int:id>')
def delete(id):
    if session.get('admin'):
        prod = Product.query.get(id)
        # Opcional: Adicionar lógica para deletar a imagem do disco
        db.session.delete(prod)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
        
