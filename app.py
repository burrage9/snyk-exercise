import sqlite3
import secrets
import requests
import re
from flask import Flask, render_template, request, url_for, flash, redirect

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.secretkey

g_output = '0'

@app.route('/')
def index():
    query = 'SELECT * FROM packages'
    packages = dbquery(query)
    return render_template('index.html', packages=packages)
    
@app.route('/results')
def results():
    global g_output
    text = ''.join(('SELECT * FROM packages WHERE id = ',str(g_output),' '))
    
    packages = dbquery(text)
    
    dep_list = diplayresults(packages)

    return(str(dep_list))

    #return render_template('results.html', packages=packages)
    
@app.route('/request', methods=('GET', 'POST'))
def requestform():
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
            getpackageinfo(name, version)

            return redirect(url_for('results'))
            
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
        g_output = '23'
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
    
def getpackageinfo(name, version):
    #when this fn ends, g_output is the row in the db of the data.
    global g_output
    ret = tablelookup(name, version)
    if ret == -1:
        # entry is not in the table, need to request it from the repo
        remotefetch(name, version)
    else:
        # entry is already in the table
        g_output = ret


def remotefetch(name, version):
    global g_output
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
                    
                    #fetch back the new row id, so it can be displayed
                    g_output = tablelookup(name, version)
                    if g_output == -1:
                        #something has gone wrong, in inserting into the table
                        return render_template('request.html')
                    
    return render_template('request.html')
    
def diplayresults(packages):
    #shouldn't just assume we're in a 1 item array
    deps = packages[0][4]
    
    start = 0
    end = 1
    i = 0
    dep_list = [0] * 100 #max number of deps?

    end = deps.find(",")
    
    while end != -1:
        dep_list[i] = deps[start:end]
        start = end + 1
        end = deps.find(",",start)
        i = i+1
        
    i=0
    while dep_list[i] != 0:
        start = 0
        end = 1
        end = dep_list[i].find(":")
        name = dep_list[i][2:(end-1)] #need to ignore quote marks
        
        version = dep_list[i][end+2:len(dep_list[i])]

        #for now we will just ignore the ~, > etc of the version number, and just find the first number character.
        m = re.search(r"\d",version)

        version = version[m.start():]
            
        getpackageinfo(name, version)
        #can trust that at this point g_output is the row in the table
        
    return dep_list
    
    
