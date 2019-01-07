from flask import Flask, render_template, flash, request
from np_config_list import HostList
import time
from dbconnect import connection
from wtforms import Form, validators, PasswordField, StringField

HOST_DICT = HostList()

time_now = time.strftime("%H:%M %m-%d-%Y")

app = Flask(__name__)
app.secret_key = 'my_secret_key'

@app.route('/')
def homepage():
    return render_template("main.html")

# Monitor Page

@app.route('/monitor/')
def monitor():
    try:
        flash("Not Logged In.")
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
    email = StringField('email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(),
                                            validators.EqualTo('confirm', message='Passwords must match.')])

@app.route('/login/', methods=['GET','POST'])
def login(): 
    try:
        return render_template("login.html")
    except Exception as e:
        return render_template("error.html", error=e)

@app.route('/register/', methods=['GET','POST'])
def register_page(): 
    try:
        c, conn = connection()
        return "ok"
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