import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
# Importar psycopg2 é bom para garantir que o Flask-SQLAlchemy o utilize
try:
    import psycopg2
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = 'tony_sports_key_secure_2025_final'

# CONFIGURAÇÕES DE SEGURANÇA
app.config['SESSION_COOKIE_HTTPONLY'] = True 
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- CONFIGURAÇÃO DE BANCO DE DADOS PARA PRODUÇÃO/DEVELOPMENT ---
# 1. Tenta usar a URL de conexão do PostgreSQL (host, Railway, Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # A biblioteca Flask-SQLAlchemy requer que a string de conexão 'postgres://' 
    # seja reescrita para 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("Conectando ao PostgreSQL de Produção.")
else:
    # 2. Se não houver DATABASE_URL, usa o SQLite local para desenvolvimento
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'tony.db')
    print("Conectando ao SQLite de Desenvolvimento.")

db = SQLAlchemy(app)

# A senha real é: Pristony22@
ADMIN_HASH = 'scrypt:32768:8:1$mQ69t2dS6yDX5Aev$77871968d46455359879a39ba22c649ebb4a0be35d2f043e1ebcabe6b8e469886d9c0bf8d1b34d6fddad2778e9e7a988bfc8ae42debd96b9c1afea9c4d7684c4'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all() # Isso cria as tabelas no DB configurado (SQLite ou Postgres)

# --- MIDDLEWARE E ROTAS (O restante do código é o mesmo) ---

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN' 
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

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
