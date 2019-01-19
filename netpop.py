from flask import Flask, render_template, flash, request, url_for, redirect, session, jsonify
from flask_mail import Mail, Message
from np_config_list import HostList
import time
import logging
from dbconnect import connection
from checks import NP_DBStatus
from quick_q import total_endpoints
from wtforms import Form, validators, PasswordField, StringField
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
from functools import wraps
from flask_executor import Executor
from os import urandom

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
executor = Executor(app)
app.secret_key = urandom(24)
app.config.update(
	DEBUG=True,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'netpopsimplemon@gmail.com',
	MAIL_PASSWORD = 'password'
	)
mail = Mail(app)

# Executor Settings
app.config['EXECUTOR_MAX_WORKERS'] = 4


# Admin Status Check
def admin_check(c_name):
    c, conn = connection()
    u_name = c_name
    admin_status = False

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

# Logs alerts and emails to cont_log table
def contact_log(recip, message_type):
    try:
        c, conn = connection()

        c.execute("INSERT INTO cont_log (recipient, date_sent, message_type) VALUES (%s, %s, %s)", 
                                                                            (thwart(recip),
                                                                            thwart(time.strftime("%H:%M:%S %m-%d-%Y")),
                                                                            thwart(message_type)))

    except Exception as e:
        app.logger.error(e)

    c.close()
    conn.close()
    gc.collect()

# Send Email
def send_mail(rec, u_name, msg_type):
    email_cont = []
    
    def message_type():
        if msg_type.lower() == "new_user":

            msg_subject = "Welcome to Netpops!"
            msg_body = f"Welcome to Netpops and Thanks for registering {u_name.capitalize()}!"

            msg = [msg_subject,msg_body]

            return msg

        elif msg_type.lower() == "reset_password":
            msg_subject = "Netpops Password Reset"
            msg_body = f"Looks like you're trying to reset your password for {uname}. Click below to reset your password.  If you did not request this password change you can ignore this message."

            msg = [msg_subject,msg_body]

            return msg

        else:
            app.logger.error("No 'msg_type' selected.")

    email_cont = message_type()


    try:
        msg = Message(email_cont[0],sender="noreply@netpopsimplemon.com",recipients=[rec])
        msg.body = email_cont[1]           
        mail.send(msg)

        contact_log(rec, msg_type)

    except Exception as e:
        app.logger.error(e)

# Login Requied - Wrapper
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)

        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))

    return wrap

# Admin Required - Wrapper
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
        c, conn = connection()

        if request.method == "POST":
            data = c.execute("SELECT * FROM users WHERE username = %s", thwart(request.form['username'],))
            data = c.fetchone()[5]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                if admin_check(session['username']):
                    session['admin_status'] = True

                flash(f"Welcome, {session['username'].capitalize()}! You are now logged in!")

                return redirect(url_for('monitor'))

                gc.collect()

            flash("Invalid Login.  Try Again.")
            return render_template("login.html")

        return render_template("login.html")

    except Exception as e:
        return render_template("error.html", error=e)


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
                c.execute("INSERT INTO users (username, password, email, rank, lastlogin) VALUES (%s, %s, %s, %s, %s)", 
                                                                                                (thwart(username),
                                                                                                thwart(password),
                                                                                                thwart(email),
                                                                                                rank,
                                                                                                time.strftime("%H:%M:%S %m-%d-%Y")))

                conn.commit()

                flash(f"Thanks for registering {username.capitalize()}!")

                c.close()
                conn.close()
                gc.collect()

                executor.submit(send_mail(email ,username, "new_user"))   
                session['logged_in'] = True
                session['username'] = username
                session['rank'] = '2'

            return redirect(url_for('monitor'))

        return render_template("register.html", form=form)

    except Exception as e:
        app.logger.error(e)
        return render_template("error.html", error=e)

# Forgot Password
@app.route('/reset_password/', methods=["GET","POST"])
def reset_password():
    try:
        c, conn = connection
        if request.method == "POST":

            x = c.execute("SELECT * FROM users WHERE username = %s"
                                ,thwart(request.form['username'],))

            if int(x) == 0:
                return render_template("reset_password.html")
                app.logger.info(f"No account found for for {request.form['username']}")
            
            else:
                data = c.execute("SELECT * FROM users WHERE username = %s"
                                        ,thwart(request.form['username'],))
                email = c.fetchone()[6]
                username = request.form['username']

                executor.submit(send_mail(email ,username, "reset_password"))

                flash("Please check you inbox for reset password instructions.")
            

        return render_template("reset_password.html")

        c.close()
        conn.close()
        gc.collect()

            
    except Exception as e:
        return render_template("error.html", error=e)



# Monitor Page
@app.route('/monitor/')
@login_required
def monitor():
    def total_endpoints():
        try:
            c, conn = connection()
            c.execute("SELECT count(*) FROM endpoints;")

            results = c.fetchone()
            results = results[0]

            c.close()
            conn.close()
            gc.collect()
            
        except Exception:
                results = 'e'

        return results

    def down_endpoints():
        try:
            c, conn = connection()
            c.execute("SELECT count(*) FROM endpoint_log WHERE endpoint_alive is FALSE;")

            results = c.fetchone()
            results = results[0]

            c.close()
            conn.close()

        except Exception:
                results = 'e'
        
        return results

    def warning_endpoints():
        try:
            c, conn = connection()
            c.execute("SELECT count(*) FROM endpoint_log WHERE warning is FALSE;")

            results = c.fetchone()
            results = results[0]

            c.close()
            conn.close()

        except Exception:
                results = 'e'
        
        return results

    try:
        return render_template("monitor.html", HOST_DICT=HOST_DICT
                                            ,time_now=time_now
                                            ,t_endpoints=total_endpoints()
                                            ,down_endpoints=down_endpoints()
                                            ,warn_endpoints=warning_endpoints())
    except Exception as e:
        app.logger.error(e)
        return render_template("error.html", error=e)

# Settings page
@app.route('/settings/')
@login_required
@admin_required
def settings():
    try:
        return render_template("settings.html", db_status=NP_DBStatus())

    except Exception as e:
        return render_template("error.html", error=e)

class AddEndpointForm(Form):
    endpoint_name = StringField('Endpoint Name')
    hostname = StringField('Hostname')
    ip_addr = StringField('IP Address')
    zip_code = StringField('Zip Code')

# Add Endpoint
@app.route('/add_endpoint/', methods=["GET", "POST"])
@login_required
@admin_required
def add_endpoint():
    try:
        form = AddEndpointForm(request.form)


        if request.method == "POST":
            c, conn = connection()

            endpoint_name = form.endpoint_name.data
            hostname = form.hostname.data
            ip_addr = form.ip_addr.data
            zip_code = form.zip_code.data

            x = c.execute("SELECT * FROM endpoints WHERE hostname = %s", (hostname,))

            if int(x) > 0:
                flash(f"{endpoint_name.capitalize()} is already in the system.")
                return render_template("add_endpoint.html", form=form)

            else:
                c.execute("INSERT INTO endpoints (endpoint_name, hostname, ip, zip, creation_date) VALUES (%s, %s, %s, %s, %s)", 
                                                                                        (thwart(endpoint_name),
                                                                                        thwart(hostname),
                                                                                        thwart(ip_addr),
                                                                                        thwart(zip_code),
                                                                                        time.strftime("%H:%M:%S %m-%d-%Y")))

            flash(f"<strong>{endpoint_name.capitalize()}</strong> has been added!")

            return redirect(url_for('monitor'))

        return render_template("add_endpoint.html", form=form)

    except Exception as e:
        app.logger.error(e)
        return render_template("error.html", error=e)




##### Playground ######
#jQuery Test Page
@app.route('/interactive/')
def interactive():
	return render_template('interactive.html')

# Background Process for jQuery page
@app.route('/background_process')
def background_process():
	try:
		lang = request.args.get('proglang', 0, type=str)
		if lang.lower() == 'python':
			return jsonify(result=time.strftime("%H:%M %m-%d-%Y"))
		else:
			return jsonify(result='Try again.')
	except Exception as e:
		return str(e)


###### end of Playground ########

# Edit Endpoint
@app.route('/edit_endpoint/', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_endpoint():
    try:
        return render_template("edit_endpoint.html")
    
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
