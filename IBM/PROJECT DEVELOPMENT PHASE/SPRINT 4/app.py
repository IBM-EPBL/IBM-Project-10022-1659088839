from curses import flash
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import tensorflow as tf
import pandas as pd
from keras.preprocessing import image
from keras.models import load_model
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

model_fruit = load_model(r"C:\IBM_Project\venv\model\fruit.h5")
model_veg = load_model(r"C:\IBM_Project\venv\model\vegetable.h5")

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'asdfghjkl'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin@1026'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = 'Please provide correct credentials'
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return render_template('Main.html', msg=msg)
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)
# this will be the logout page


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return render_template('index.html', msg='')

# this will be the registration page, we need to use both GET and POST requests


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                'INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# this will be the home page, only accessible for loggedin users


@app.route('/Main', methods=['GET', 'POST'])
def Main():

    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('Main.html', username=session['username'])

    # User is not loggedin redirect to login page
    return render_template('index.html', msg='')

# this will be the profile page, only accessible for loggedin users


@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s',
                       (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/predict', methods=['POST'])
def predict():
    mytext = []
    text = []
    plant = []
    mypath = []
    file_path = []
    if request.method == "POST":
        f = request.files['image']
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', f.filename)
        f.save(file_path)

        img = image.load_img(file_path, target_size=(128, 128))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        plant = request.form['plant']
        if (plant == "fruit"):
            y = np.argmax(model_fruit.predict(x), axis=1)
            predict = ['Apple___Black_rot', 'Apple___healthy',
                     'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Peach___Bacterial_spot', 'Peach___healthy']
            df = pd.read_excel('precautions - fruits.xlsx')
            text = df.iloc[y[0]]['caution']
            print(df.iloc[y[0]]['caution'])
        else:
            y = np.argmax(model_veg.predict(x), axis=1)
            predict = ['Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight', 'Potato___healthy',
                     'Potato___Late_blight', 'Tomato___Bacterial_spot', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot']
            df = pd.read_excel('precautions - veg.xlsx')
            text = df.iloc[y[0]]['caution']
    return render_template('Main.html', mytext=text, mypath=file_path)


if __name__ == '__main__':
    app.run(debug=True)
