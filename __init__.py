from flask import Flask, render_template, flash
from np_config_list import HostList
import time

HOST_DICT = HostList()

time_now = time.strftime("%H:%M %m-%d-%Y")

app = Flask(__name__)
app.secret_key = 'my_secret_key'

@app.route('/')
def homepage():
    return render_template("main.html")

@app.route('/monitor/')
def monitor():
    try:
        flash("Not Logged In.")
        return render_template("monitor.html", HOST_DICT = HOST_DICT, time_now = time_now)
    except Exception as e:
        return render_template("error.html", error=e)

@app.route('/settings/')
def settings():
    try:
        return render_template("settings.html")
    except Exception as e:
        return render_template("error.html", error=e)

@app.route('/login/')
def login():
    try:
        return render_template("login.html")
    except Exception as e:
        return render_template("error.html", error=e)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(500)
def server_issue(e):
    return render_template("500.html", error=e)

if __name__ == '__main__':
    app.run(debug=True)