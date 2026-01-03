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

# 1. Dashboard
@app.route("/")
def home():
    eh_novo_usuario = request.args.get('novo')
    if 'usuario_nome' in session:
        return render_template("index.html", 
                               nome=session['usuario_nome'], 
                               novo_usuario=eh_novo_usuario)
    return render_template("index.html")

# 2. Lista de Livros (COM BUSCA 🔍)
@app.route("/livros")
def livros():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    id_do_dono = session['usuario_id']
    
    # 1. Pega o termo que veio da barra de pesquisa (se houver)
    termo = request.args.get('q')
    
    # 2. Começa a consulta filtrando APENAS pelos livros do dono logado
    query = Livro.query.filter_by(usuario_id=id_do_dono)
    
    # 3. Se tiver termo de busca, adiciona um filtro extra pelo título
    if termo:
        # 'contains' verifica se o termo está dentro do título
        query = query.filter(Livro.titulo.contains(termo))
    
    # 4. Executa a busca no banco e pega os resultados
    meus_livros = query.all()
    
    # Enviamos 'termo_busca' de volta para o HTML para ele continuar escrito na caixinha
    return render_template("livros.html", livros=meus_livros, termo_busca=termo)

# 3. Criar Livro
@app.route("/criar", methods=["GET", "POST"])
def criar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        titulo = request.form['titulo']
        autor = request.form['autor']
        dono = session['usuario_id'] # Pega o ID de quem está logado
        
        # Cria o livro já carimbando quem é o dono
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
    
    # Segurança: Se o livro não for seu, você é expulso
    if livro.usuario_id != session['usuario_id']:
        return "<h3>Acesso Negado: Este livro pertence a outro usuário!</h3>"

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
    
    # Segurança
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