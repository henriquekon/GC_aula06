from flask import Flask, jsonify, request, session
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'secret-key-ultra-top-secret'
CORS(app)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'postgres'),
    'port': 5432,
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres'),
    'database': os.environ.get('DB_NAME', 'receitas')
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    login = data.get('login')
    senha = data.get('senha')
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM usuario WHERE login = %s AND senha = %s", (login, senha))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['nome']
        return jsonify({'success': True, 'user': user['nome']})
    return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/receitas', methods=['GET'])
def get_receitas():
    tipo = request.args.get('tipo')
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    if tipo and tipo in ['doce', 'salgada']:
        cur.execute("SELECT * FROM receita WHERE tipo_receita = %s", (tipo,))
    else:
        cur.execute("SELECT * FROM receita")
    
    receitas = []
    for row in cur.fetchall():
        r = dict(row)
        r['custo'] = float(r['custo'])
        receitas.append(r)
    cur.close()
    conn.close()
    return jsonify(receitas)

@app.route('/api/receitas/<string:nome>', methods=['GET'])
def get_receita_nome(nome):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM receita WHERE nome ILIKE %s", (nome,))
    receitas = cur.fetchall()
    cur.close()
    conn.close()

    if receitas:
        receitas_json = []
        for r in receitas:
            r_dict = dict(r)
            r_dict['custo'] = float(r_dict['custo'])
            receitas_json.append(r_dict)
        return jsonify(receitas_json)
    return jsonify({'error': 'Nenhuma receita encontrada'}), 404

@app.route('/api/receitas/<int:id>', methods=['GET'])
def get_receita(id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM receita WHERE id = %s", (id,))
    receita = cur.fetchone()
    cur.close()
    conn.close()
    
    if receita:
        r = dict(receita)
        r['custo'] = float(r['custo'])
        return jsonify(r)
    return jsonify({'error': 'Receita não encontrada'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)