from flask import Flask, render_template, flash, request, url_for, redirect, session
from np_config_list import HostList
import time
from dbconnect import connection
from wtforms import Form, validators, PasswordField, StringField
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc


# Random Variables
HOST_DICT = HostList()
time_now = time.strftime("%H:%M %m-%d-%Y")

# Settings
app = Flask(__name__)
app.secret_key = 'my_secret_key'

###
# Routes
###

# Home Page
@app.route('/')
def homepage():
    return render_template("main.html")

# Monitor Page

@app.route('/monitor/')
def monitor():
    try:
        return render_template("monitor.html", HOST_DICT=HOST_DICT, time_now=time_now)
    except Exception as e:
        return render_template("error.html", error=e)

# Settings page

@app.route('/settings/')
def settings():
    try:
        return render_template("settings.html")
    except Exception as e:
        return render_template("error.html", error=e)

# Login/Register Page

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=20)])
    email = StringField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(),
                                            validators.EqualTo('confirm', message='Passwords must match.')])
    confirm = PasswordField('Corfirm Password')


@app.route('/login/', methods=['GET','POST'])
def login(): 
    try:
        return render_template("login.html")
    except Exception as e:
        return render_template("error.html", error=e)

@app.route('/register/', methods=['GET','POST'])
def register_page(): 
    try:
        form = RegistrationForm(request.form)
        c,conn = connection()

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.hash((str(form.password.data)))

            x = c.execute("SELECT * FROM users WHERE username = %s", (username,))

            if int(x) > 0:
                flash("Username taken. Try another!")
                return render_template("register.html", form=form)

            else:
                c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",(thwart(username), thwart(password), thwart(email)))

                conn.commit()

                flash("Thanks for Registering")

                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

            return redirect(url_for('monitor'))

        return render_template("register.html", form=form)

    except Exception as e:
        return render_template("error.html", error=e)

# Error Handling

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