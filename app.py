from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>BookKeeper está vivo!</h1><p>Sistema iniciando...</p>"

if __name__ == "__main__":
    app.run(debug=True)