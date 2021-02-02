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
MAX_DEPS = 1000 #this should go in a config file - also we need to somehow calculate what this value is

@app.route('/')
def index():
    #Homepage prints the full results of the DB
    query = 'SELECT * FROM packages'
    packages = dbquery(query)
    return render_template('index.html', packages=packages)
    
@app.route('/results')
def results():
    # Results prints the dependency list of the requested package

    global g_output  # using this global as a messy hack to pass around the row of the package in the DB.
    text = ''.join(('SELECT * FROM packages WHERE id = ',str(g_output),' '))
    
    packages = dbquery(text)
    
    dep_list = diplayresults(packages)

    return(str(dep_list))

    #return render_template('results.html', packages=packages)
    
@app.route('/request', methods=('GET', 'POST'))
def requestform():
    # The request form allows the user to enter a package name and version
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
            flash('Name is required!') #we should check for version being present too
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
        return data[0]['id']
        
def dbinsert(message, name, version, dependencies):
    #pushes a package into the SQL DB
    conn = get_db_connection()
    conn.execute(message,(name, version,dependencies))
    conn.commit()
    conn.close()

def dbquery(message):
    # makes a call to the SQL DB using a preconstructed text string
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

    #Make sure we had a connection
    if r.status_code != 200:
        flash('Error connecting to NPM registry')
        return render_template('index.html')

    #check if there are any dependencies
    findret = r.text.find("""dependencies""")
    if findret == -1:
        return render_template('request.html')

    #find the open bracket - the start of the dependencies
    i = findret
    start = r.text.find("{",i)
    if start == -1:
        flash('Dependencies, but no dependencies ?!?')
        return render_template('request.html')
        
    #find the close bracket - the end of the dependencies
    end = r.text.find("}",start)
    if end == -1:
        flash('Open brackets but no close brackets?!?')
        return render_template('request.html')

    # Push the retrieved list into our DB
    dep_list = r.text[start+1:end]
    dbinsert('INSERT INTO packages (name, version,dependencies) VALUES (?,?,?)',name, version, dep_list)
    
    #fetch back the new row id, so it can be displayed
    g_output = tablelookup(name, version)
    if g_output == -1:
        #something has gone wrong, in inserting into the table
        return render_template('request.html')
                    
    
    
def diplayresults(packages):
    # recursively fetches the dependencies of 'packages[0]' populating them into out_list which is returned
    global g_output
    #shouldn't just assume we're in a 1 item array
    deps = packages[0][4]
    
    start = 0
    end = 1
    i = 0
    count = 0
    in_list = [0] * MAX_DEPS #max number of deps?
    out_list = [0] * MAX_DEPS #max number of deps?

    end = deps.find(",")
    
    #populate the list with the list of the dependencies of the highest level package.
    while end != -1:
        in_list[i] = deps[start:end]
        start = end + 1
        end = deps.find(",",start)
        i = i+1
        
    #hack to include the last entry in the list (which doesn't have a following ',')
    in_list[i] = deps[start:]
    i=0
    
    #walk the list, adding new entries for every package
    while (in_list[i] != 0):
        out_list[count] = in_list[i][1:-1]
        count = count + 1

        start = 0
        end = in_list[i].find(":")
        name = in_list[i][1:(end-1)] #offset is because we need to ignore quote marks
        
        version = in_list[i][end+2:-1]

        #for now we will just ignore the ~, > etc of the version number, and just find the first numeric character.
        m = re.search(r"\d",version)

        formatedversion = version[m.start():]

        getpackageinfo(name, formatedversion)
        #can trust that at this point g_output is the row in the table
        
        text = ''.join(('SELECT dependencies FROM packages WHERE id = ',str(g_output),' '))
        subdeps = dbquery(text)

        #for each dependency add it to our output list, 
        for subdep in subdeps:
            out_list[count] = subdep[0]
            count = count + 1
            
        i=i+1
        
    return out_list
    
    
