from flask import Flask, render_template, flash, request, url_for, redirect, session
from np_config_list import HostList
import time
import logging
from dbconnect import connection
from wtforms import Form, validators, PasswordField, StringField
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
from functools import wraps
from flask_executor import Executor

# Random Variables
HOST_DICT = HostList()
time_now = time.strftime("%H:%M %m-%d-%Y")

####
# Settings
####

# Logging Settings
logging.basicConfig(level=logging.DEBUG,
                    filename="netpop.log",
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Flask Settings
app = Flask(__name__)
app.secret_key = 'my_secret_key'
app.debug = True
app.config['EXECUTOR_MAX_WORKERS'] = 4

executor = Executor(app)


def admin_check(c_name):
    c, conn = connection()
    u_name = c_name

    try:
        data = c.execute("SELECT * FROM users WHERE username = %s", u_name,)
        user_rank = c.fetchone()[8]
        if user_rank >= 3:
            session['user_rank'] = '3'
            session['admin_status'] = True
            session.modified = True

            admin_status = True

    except Exception:
        admin_status = False
    c.close()
    conn.close()
    gc.collect()

    return admin_status


# Wrappers
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)

        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))

    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if admin_check(session['username']) == True:
            return f(*args, **kwargs)

        else:
            return redirect(url_for('access_denied'))

    return wrap

###
# Routes
###

# Home Page
@app.route('/')
def homepage():
    return render_template("main.html")

# Logout Page
@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You've been logged out")
    gc.collect()
    return redirect(url_for('homepage'))

# Login Page
@app.route('/login/', methods=["GET", "POST"])
def login_page():

    try:
        error = ""
        c, conn = connection()

        if request.method == "POST":
            data = c.execute("SELECT * FROM users WHERE username = %s", thwart(request.form['username'],))
            data = c.fetchone()[5]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                if admin_check(session['username']):
                    session['admin_status'] = True

                flash("You are now logged in!")

                return redirect(url_for('monitor'))

        gc.collect()

        return render_template("login.html")

    except Exception as e:
        flash(f"Login Error.  Try Again!")
        return render_template("login.html")


# Registration Page
class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=20)])
    email = StringField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(),
                                          validators.EqualTo('confirm', message='Passwords must match.')])
    confirm = PasswordField('Confirm Password')

# Register Page
@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    rank = '2' # (Sets all users as Standard Users on registration)

    try:
        form = RegistrationForm(request.form)
        c, conn = connection()

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.hash((str(form.password.data)))

            x = c.execute("SELECT * FROM users WHERE username = %s", (username,))

            if int(x) > 0:
                flash("That username is taken. Try another!")
                return render_template("register.html", form=form)

            else:
                c.execute("INSERT INTO users (username, password, email, rank) VALUES (%s, %s, %s, %s)", (thwart(username),
                                                                                                thwart(password),
                                                                                                thwart(email),
                                                                                                rank))

                conn.commit()

                flash(f"Thanks for registering {username}!")

                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username
                session['rank'] = '2'

            return redirect(url_for('monitor'))

        return render_template("register.html", form=form)

    except Exception as e:
        return render_template("error.html", error=e)


# Monitor Page
@app.route('/monitor/')
@login_required
def monitor():
    try:
        return render_template("monitor.html", HOST_DICT=HOST_DICT, time_now=time_now)
    except Exception as e:
        return render_template("error.html", error=e)


# Settings page
@app.route('/settings/')
@login_required
@admin_required
def settings():
    try:
        return render_template("settings.html")

    except Exception as e:
        return render_template("error.html", error=e)
        

@app.route('/add_endpoint/', methods=['GET', 'POST'])
@login_required
@admin_required
def add_endpoint():
    try:
        return render_template("add_endpoint.html")
    
    except Exception as e:
        return render_template("error.html", error=e)


# Error Handling
@app.route('/access_denied/')
def access_denied():
    return render_template("access_denied.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


@app.errorhandler(405)
def page_not_found(e):
    return render_template("405.html")


@app.errorhandler(500)
def server_issue(e):
    return render_template("500.html", error=e)


# Main App
if __name__ == '__main__':
    app.run(debug=True)
    executor.init_app(app)
