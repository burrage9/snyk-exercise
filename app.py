import sqlite3
import secrets
from flask import Flask, render_template, request, url_for, flash, redirect

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.secretkey

@app.route('/')
def index():
    conn = get_db_connection()
    packages = conn.execute('SELECT * FROM packages').fetchall()
    conn.close()
    return render_template('index.html', packages=packages)
    
@app.route('/request', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        name = request.form['name']
        version = request.form['version']

        if not name:
            flash('Name is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO packages (name, version,dependencies) VALUES (?,?,?)',
                         (name, version,""))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('request.html')
    
    
   
