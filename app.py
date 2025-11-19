import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from io import BytesIO
from PIL import Image

# --- CONFIGURAÇÃO DE AMBIENTE E SEGURANÇA ---
app = Flask(__name__)
app.secret_key = 'tony_sports_key_secure_2025_final'

# CONFIGURAÇÕES DE SEGURANÇA
app.config['SESSION_COOKIE_HTTPONLY'] = True 
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 

# Remove a configuração de UPLOAD_FOLDER (não será mais usada)
# app.config['UPLOAD_FOLDER'] = '...' 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limite de 16MB

# --- CONFIGURAÇÃO DE BANCO DE DADOS ---
# Tenta usar a URL de conexão do PostgreSQL (DATABASE_URL)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'tony.db')

db = SQLAlchemy(app)

# A senha real é: Pristony22@
ADMIN_HASH = generate_password_hash('Pristony22@')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    # O campo 'image' agora armazena a string Base64 da imagem
    image = db.Column(db.Text, nullable=False) 
    price = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()

# --- MIDDLEWARE DE SEGURANÇA (HEADERS) ---
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

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
            try:
                # 1. Abre a imagem usando PIL
                img = Image.open(file)
                # 2. Converte para JPEG e cria um buffer
                buffer = BytesIO()
                img.save(buffer, format="JPEG")
                # 3. Codifica o buffer em Base64
                encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # SALVA A STRING BASE64 NO CAMPO 'image' DO DB
                new_prod = Product(name=request.form['name'], category=request.form['category'], price=float(request.form['price']), image=encoded_string)
                
                db.session.add(new_prod)
                db.session.commit()
                flash('Produto salvo (Base64) com sucesso!', 'success')
            except Exception as e:
                # Se a imagem for muito grande ou o formato for ruim
                flash(f'Erro ao processar imagem. Tente uma foto menor ou diferente. Erro: {e}', 'error')
                
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin.html', products=products)

@app.route('/delete/<int:id>')
def delete(id):
    if session.get('admin'):
        prod = Product.query.get(id)
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
                
