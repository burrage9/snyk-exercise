import sqlite3
import secrets
import requests
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

        """
        # working code to keep the db tidy while we do testing
        conn = get_db_connection()
        conn.execute("DELETE FROM packages WHERE name='express'")
        conn.commit()
        conn.close()
        """

        if not name:
            flash('Name is required!') #should we check for version too?
        else:
            ret = tablelookup(name, version)
            if ret == -1:
                # entry is not in the table, need to request it from the repo
                remotefetch(name, version)
                return render_template('request.html')
            
            else:
                # entry is already in the table
                return redirect(url_for('index'))                   
            
    return render_template('request.html')
    
    
    
def tablelookup(name, version):
    # return -1 if not found, else index in table
    conn = get_db_connection()
    query = ''.join(('SELECT * FROM packages WHERE name = "',name,'" AND version = "',version,'"'))
    data = dbquery(query)
    conn.close()
   
    if not data:
        return -1
    else:
        return data[0]['id']
        
def dbinsert(message, name, version, dependencies):
    conn = get_db_connection()
    conn.execute(message,(name, version,dependencies))
    conn.commit()
    conn.close()

def dbquery(message):
    conn = get_db_connection()
    ret = conn.execute(message).fetchall()
    conn.commit()
    conn.close()
    return ret

def remotefetch(name, version):
    url = ''.join(('https://registry.npmjs.org/',name,'/',version))
    r = requests.get(url)

    if r.status_code != 200:
        flash('Error connecting to NPM registry')
    else:
        i = r.text.find("""dependencies""")
        if i == -1:
            return render_template('request.html')
        else:
            start = r.text.find("{",i)
            if start == -1:
                flash('Dependencies, but no dependencies ?!?')
                return render_template('request.html')
            else:
                end = r.text.find("}",start)
                if end == -1:
                    flash('Open brackets but no close brackets?!?')
                    return render_template('request.html')
                else:
                    dep_list = r.text[start+1:end]
                    dbinsert('INSERT INTO packages (name, version,dependencies) VALUES (?,?,?)',name, version, dep_list)
                    return redirect(url_for('index'))
                    
    return render_template('request.html')
    
   
