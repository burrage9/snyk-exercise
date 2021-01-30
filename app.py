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
                return render_template('request.html')
            
            url = ''.join(('https://registry.npmjs.org/',name,'/',version))
            r = requests.get(url)
        
            """"
            conn = get_db_connection()
            conn.execute('INSERT INTO packages (name, version,dependencies) VALUES (?,?,?)',
                         (name, version,r.text))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
            """

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
                            conn = get_db_connection()
                            conn.execute('INSERT INTO packages (name, version,dependencies) VALUES (?,?,?)',
                                         (name, version,dep_list))
                            conn.commit()
                            conn.close()
                            return redirect(url_for('index'))
                    


    return render_template('request.html')
    
    
    
def tablelookup(name, version):
    # return -1 if not found, else index in table
    conn = get_db_connection()
    query = ''.join(('SELECT * FROM packages WHERE name = "',name,'" AND version = "',version,'"'))
    #query = ''.join(('SELECT * FROM packages WHERE name = "express"'))
    data = conn.execute(query).fetchall()
    conn.close()
   
    if not data:
        return -1
    else:
        return data[0]['id']
        


    
   
