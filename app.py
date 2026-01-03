from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
app.secret_key = 'chave-secreta-do-bookkeeper'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookkeeper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (Tabelas) ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Disponível')
    
    # Coluna que liga o livro ao dono
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

# --- ROTAS ---

# 1. Dashboard (AGORA COM ESTATÍSTICAS 📊)
@app.route("/")
def home():
    eh_novo_usuario = request.args.get('novo')
    
    # Se o usuário estiver logado, calculamos os números dele
    if 'usuario_id' in session:
        id_dono = session['usuario_id']
        
        # Conta TODOS os livros desse usuário
        total_livros = Livro.query.filter_by(usuario_id=id_dono).count()
        
        # Conta só os EMPRESTADOS
        total_emprestados = Livro.query.filter_by(usuario_id=id_dono, status='Emprestado').count()
        
        # Conta só os DISPONÍVEIS
        total_disponiveis = Livro.query.filter_by(usuario_id=id_dono, status='Disponível').count()
        
        return render_template("index.html", 
                               nome=session['usuario_nome'], 
                               novo_usuario=eh_novo_usuario,
                               total=total_livros,
                               emprestados=total_emprestados,
                               disponiveis=total_disponiveis)
                               
    # Se não estiver logado, mostra a tela normal sem números
    return render_template("index.html")

# 2. Lista de Livros (COM BUSCA 🔍)
@app.route("/livros")
def livros():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    id_do_dono = session['usuario_id']
    termo = request.args.get('q')
    
    # Começa filtrando pelo dono
    query = Livro.query.filter_by(usuario_id=id_do_dono)
    
    # Se tiver busca, filtra também pelo título
    if termo:
        query = query.filter(Livro.titulo.contains(termo))
    
    meus_livros = query.all()
    
    return render_template("livros.html", livros=meus_livros, termo_busca=termo)

# 3. Criar Livro
@app.route("/criar", methods=["GET", "POST"])
def criar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        titulo = request.form['titulo']
        autor = request.form['autor']
        dono = session['usuario_id']
        
        novo_livro = Livro(titulo=titulo, autor=autor, usuario_id=dono)
        
        db.session.add(novo_livro)
        db.session.commit()
        return redirect(url_for('livros'))
        
    return render_template("criar.html")

# 4. Editar Livro
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'usuario_nome' not in session:
        return redirect(url_for('login'))

    livro = Livro.query.get_or_404(id)
    
    if livro.usuario_id != session['usuario_id']:
        return "<h3>Acesso Negado!</h3>"

    if request.method == 'POST':
        livro.titulo = request.form['titulo']
        livro.autor = request.form['autor']
        livro.status = request.form['status']
        db.session.commit()
        return redirect(url_for('livros'))

    return render_template('editar.html', livro=livro)

# 5. Excluir Livro
@app.route('/excluir/<int:id>')
def excluir(id):
    if 'usuario_nome' not in session:
        return redirect(url_for('login'))
        
    livro = Livro.query.get_or_404(id)
    
    if livro.usuario_id != session['usuario_id']:
        return "<h3>Acesso Negado!</h3>"
        
    db.session.delete(livro)
    db.session.commit()
    return redirect(url_for('livros'))

# 6. Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.senha == senha:
            session['usuario_nome'] = usuario.nome
            session['usuario_id'] = usuario.id
            return redirect(url_for('home'))
        else:
            return "<h3>Erro: Email ou senha incorretos! <a href='/login'>Tentar de novo</a></h3>"
    return render_template("login.html")

# 7. Registro
@app.route("/registrar", methods=["POST"])
def registrar():
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    if Usuario.query.filter_by(email=email).first():
        return "<h3>Erro: Email já cadastrado! <a href='/login'>Voltar</a></h3>"
        
    novo_usuario = Usuario(nome=nome, email=email, senha=senha)
    db.session.add(novo_usuario)
    db.session.commit()
    
    session['usuario_nome'] = novo_usuario.nome
    session['usuario_id'] = novo_usuario.id
    
    return redirect(url_for('home', novo=1))

# 8. Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)