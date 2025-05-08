from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret123'  # Assurez-vous de le changer pour un secret plus sûr en production
DB_NAME = 'passengers.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            passport TEXT NOT NULL,
            destination TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        hashed = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            flash('Inscription réussie. Connectez-vous.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Ce nom d’utilisateur existe déjà.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/dashboard')
        else:
            flash('Identifiants invalides.', 'error')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    if request.method == 'POST':
        name = request.form['name'].strip()
        passport = request.form['passport'].strip()
        destination = request.form['destination'].strip()
        if name and passport and destination:
            conn.execute('INSERT INTO passengers (user_id, name, passport, destination) VALUES (?, ?, ?, ?)',
                         (session['user_id'], name, passport, destination))
            conn.commit()
            flash('Voyageur ajouté.', 'success')
        else:
            flash('Tous les champs sont requis.', 'error')

    passengers = conn.execute('SELECT * FROM passengers WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', passengers=passengers)

@app.route('/delete/<int:id>')
def delete_passenger(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    conn.execute('DELETE FROM passengers WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Voyageur supprimé.', 'success')
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnexion réussie.', 'success')
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)

