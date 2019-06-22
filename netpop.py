import configparser
from flask import Flask, render_template, flash, request, url_for, redirect, session, jsonify
from flask_mail import Mail, Message
from np_config_list import HostList  # get rid of this
import time
from dbconnect import connection
from checks import NP_DBStatus
from wtforms import Form, validators, PasswordField, StringField
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
from functools import wraps
from flask_executor import Executor
from os import urandom
import secrets
from secrets import token_urlsafe

# Random Variables
HOST_DICT = HostList()  # and get rid of this
time_now = time.strftime("%H:%M %m-%d-%Y")

####
# Settings
####
config = configparser.ConfigParser()
config.read('conf/config.ini')

netpop_hostname = config['NETPOP']['HOSTNAME']
netpop_logging_to_console = config['NETPOP']['LOG_TO_CONSOLE']

# Logging Settings
if netpop_logging_to_console == 1:
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        filename="netpop.log",
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

# Flask Settings
app = Flask(__name__)
executor = Executor(app)
app.secret_key = urandom(24)
app.config.update(
    # Disabled for dev
    # SESSION_COOKIE_SECURE = True,
    # REMEMBER_COOKIE_SECURE = True,
    DEBUG=True,
    # EMAIL SETTINGS
    MAIL_SERVER=config['EMAIL']['EMAIL_SERVER'],
    MAIL_PORT=config['EMAIL']['EMAIL_PORT'],
    MAIL_USE_SSL=config['EMAIL']['EMAIL_USE_SSL'],
    MAIL_USERNAME=config['EMAIL']['EMAIL_USERNAME'],
    MAIL_PASSWORD=config['EMAIL']['EMAIL_PASSWORD'])

mail = Mail(app)

# Executor Settings
app.config['EXECUTOR_MAX_WORKERS'] = 4


# Admin Status Check
def admin_check(c_name):
    c, conn = connection()
    u_name = thwart(c_name)
    admin_status = False

    try:
        data = c.execute("SELECT * FROM users WHERE username = %s", u_name, )
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


# Verify user has a valid token before allowing access to the update password page for their account.
def token_check(c_token):
    c, conn = connection()
    token_status = False
    try:
        x = c.execute("SELECT * FROM users WHERE reset_token = %s", c_token, )

        if int(x) == 0:
            token_status = False

        else:
            token_status = True

    except Exception:
        token_status = False

    c.close()
    conn.close()
    gc.collect()

    return token_status


# Logs alerts and emails to cont_log table
def contact_log(recip, message_type):
    try:
        c, conn = connection()

        c.execute("INSERT INTO cont_log (recipient, date_sent, message_type) VALUES (%s, %s, %s)",
                  (thwart(recip), thwart(time.strftime("%H:%M:%S %m-%d-%Y")), thwart(message_type)))
        conn.commit()

    except Exception as e:
        if netpop_logging_to_console == 1:
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

            msg = [msg_subject, msg_body]

            print("Welcome Email Sent.")

            return msg

        elif msg_type.lower() == "reset_password":
            c, conn = connection()

            data = c.execute("SELECT * FROM users WHERE username = %s", u_name, )
            result = c.fetchone()

            token = result[11]

            full_url = f"{netpop_hostname}/reset_password/{token}"

            msg_subject = "NetPops Password Reset"
            msg_html = f'<p>Hey {u_name.capitalize()}!\
                            <br>\
                            We got a request to reset your password.\
                            <br>\
                            <p>Click <a href="{full_url}">HERE</a> to it.\
                            <br>\
                            <p>Or open this <strong>{full_url}</strong> in your browser.\
                            <br>\
                            <p>If you did not request this password reset, then just ignore this email.\
                            <br>\
                            Thanks!\
                            <br>\
                            NetPops</p>'

            msg_body = f"Looks like you're trying to reset your password for {u_name}. \
                        Go to {full_url} to reset you password.  If you did not request \
                        this password change you can ignore this message."

            msg = [msg_subject, msg_body, msg_html]

            return msg

        elif msg_type.lower() == "password_update_confirm":
            c, conn = connection()
            data = c.execute("SELECT * FROM users WHERE username = %s", u_name, )

            msg_subject = "NetPops Password Changed"
            msg_html = f'<p>Hey {u_name.capitalize()}!\
                            <br>\
                            Your password was successfully changed!\
                            <br>\
                            Thanks!\
                            <br>\
                            NetPop</p>'

            msg_body = "Your password was successfully changed! Thanks!"

            msg = [msg_subject, msg_body, msg_html]

            return msg

        else:
            if netpop_logging_to_console == 1:
                app.logger.error(e)

    email_cont = message_type()

    try:
        msg = Message(email_cont[0], sender="noreply@netpopsimplemon.com", recipients=[rec])
        msg.body = email_cont[1]
        msg.html = email_cont[2]
        mail.send(msg)

        contact_log(rec, msg_type)

    except Exception as e:
        if netpop_logging_to_console == 1:
            app.logger.error(e)


################
### Wrappers ###
################

# Login Required - Wrapper
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


# Token Required - Wrapper
def token_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if token_check(session['token']) == True:
            return f(*args, **kwargs)

        else:
            return redirect(url_for('access_denied'))

    return wrap


##############
### Routes ###
##############

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
    return redirect(url_for('homepage'))


# Login Page
@app.route('/login/', methods=["GET", "POST"])
def login_page():
    try:
        c, conn = connection()

        if request.method == "POST":
            secure_un = thwart(request.form['username'], )

            data = c.execute("SELECT * FROM users WHERE username = %s", secure_un)
            data = c.fetchone()[5]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                if admin_check(session['username']):
                    session['admin_status'] = True
                else:
                    session['admin_status'] = False

                c.execute("UPDATE users SET lastlogin=%s WHERE username=%s",
                          (time.strftime("%H:%M:%S %m-%d-%Y"), secure_un))
                conn.commit()

                flash(f"Welcome, {session['username'].capitalize()}! You are now logged in!")
                return redirect(url_for('monitor'))

                gc.collect()

            if netpop_logging_to_console:
                app.logger.info(f"No user found for {request.form['username']}")

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
                                          validators.EqualTo('confirm', message='Passwords do not match.')])
    confirm = PasswordField('Confirm Password')


@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    rank = '2'  # (Sets all users as Standard Users on registration)

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
                c.execute(
                    "INSERT INTO users (username, password, email, rank, lastlogin, account_creation) VALUES (%s, %s, %s, %s, %s, %s)",
                    (thwart(username),
                     thwart(password),
                     thwart(email),
                     rank,
                     time.strftime("%H:%M:%S %m-%d-%Y"),
                     time.strftime("%H:%M:%S %m-%d-%Y")))

                conn.commit()

                flash(f"Thanks for registering {username.capitalize()}!")

                c.close()
                conn.close()
                gc.collect()

                print("Sending Welcome Email.")
                executor.submit(send_mail(email, username, "new_user"))
                session['logged_in'] = True
                session['username'] = username
                session['rank'] = '2'

            return redirect(url_for('monitor'))

        return render_template("register.html", form=form)

    except Exception as e:
        if netpop_logging_to_console == 1:
            app.logger.error(e)

        # return render_template("error.html", error=e)
        return e


# Forgot Password
@app.route('/reset_password/', methods=["GET", "POST"])
def reset_password():
    try:
        c, conn = connection()
        if request.method == "POST":

            x = c.execute("SELECT * FROM users WHERE username = %s", thwart(request.form['username'], ))

            if int(x) == 0:
                app.logger.info(f"No account found for for {request.form['username']}")
                return render_template("reset_password.html")

            else:
                data = c.execute("SELECT * FROM users WHERE username = %s", thwart(request.form['username'], ))
                email = c.fetchone()[6]
                username = request.form['username']
                secure_un = thwart(username.lower())
                token = secrets.token_urlsafe(32)
                secure_token = thwart(token)

                c.execute("UPDATE users SET reset_token=%s WHERE username=%s", (secure_token, secure_un))
                c.execute("UPDATE users SET reset_password=%s WHERE username=%s", (1, secure_un))

                conn.commit()

                executor.submit(send_mail(email, username, "reset_password"))

                flash(f"Please check your inbox for reset password instructions for {username}.")
                return redirect(url_for('homepage'))

        return render_template("reset_password.html")

        c.close()
        conn.close()
        gc.collect()

    except Exception as e:
        return render_template("error.html", error=e)


# Reset Password Token reply
@app.route('/reset_password/<token>')
def reset_password_token(token):
    try:
        c, conn = connection()
        x = c.execute("SELECT * FROM users WHERE reset_token = %s", token)

        if int(x) == 0:
            app.logger.info(f"No token found for for {token}")
            return 404

        else:
            session['token'] = token
            return redirect(url_for('update_password'))

    except Exception as e:
        return render_template("error.html", error=e)


# Change/Update Password Page
@app.route('/update_password/', methods=["GET", "POST"])
@token_required
def update_password():
    try:
        c, conn = connection()

        if request.method == "POST":

            c, conn = connection()
            token = session['token']

            data = c.execute("SELECT * FROM users WHERE reset_token = %s", (thwart(token),))
            result = c.fetchone()
            username = result[3]
            email = result[6]
            password = request.form['password']
            c_password = request.form['c_password']
            hashed_password = sha256_crypt.hash(password)

            if password == c_password:

                c.execute("UPDATE users SET password=%s WHERE username=%s", (thwart(hashed_password), username))
                c.execute("UPDATE users SET reset_token=NULL WHERE username=%s", (username))
                c.execute("UPDATE users SET reset_password=0 WHERE username=%s", (username))

                conn.commit()

                session.pop('token')
                executor.submit(send_mail(email, username, "password_update_confirm"))

                flash("Your password has been changed! Try your login now.")
                return redirect(url_for('login_page'))

            else:
                flash("Uh-Oh... Your passwords didn't match.  Let's try that again.")
                return redirect(url_for('update_password'))

        return render_template("update_password.html")

        c.close()
        conn.close()
        gc.collect()

    except Exception as e:
        # return e
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

    def host_list():
        try:
            c, conn = connection()
            c.execute("SELECT endpoint_name FROM netpop.endpoints;")

            results = [item[0] for item in c.fetchall()]

            c.close()
            conn.close()

        except Exception:
            results = 'e'

        return results

    try:
        return render_template("monitor.html", host_dict=host_list(), time_now=time_now, t_endpoints=total_endpoints(),
                               down_endpoints=down_endpoints(), warn_endpoints=warning_endpoints())
    except Exception as e:
        if netpop_logging_to_console == 1:
            app.logger.error(e)

        # return render_template("error.html", error=e)
        return e


# Settings page (Admin only)
@app.route('/settings/')
@login_required
@admin_required
def settings():
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

    try:
        return render_template("settings.html", db_status=NP_DBStatus(), t_endpoints=total_endpoints())

    except Exception as e:
        return render_template("error.html", error=e)


# Add Endpoint (Admin Only)
class AddEndpointForm(Form):
    endpoint_name = StringField('Endpoint Name')
    hostname = StringField('Hostname')
    ip_addr = StringField('IP Address')
    zip_code = StringField('Zip Code')


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
                c.execute(
                    "INSERT INTO endpoints (endpoint_name, hostname, ip, zip, creation_date) VALUES (%s, %s, %s, %s, %s)",
                    (thwart(endpoint_name),
                     thwart(hostname),
                     thwart(ip_addr),
                     thwart(zip_code),
                     time.strftime("%H:%M:%S %m-%d-%Y")))
                conn.commit()

            flash(f"{endpoint_name.capitalize()} has been added!")

            return redirect(url_for('monitor'))

        return render_template("add_endpoint.html", form=form)

    except Exception as e:
        if netpop_logging_to_console == 1:
            app.logger.error(e)

        return render_template("error.html", error=e)


# My Profile/Account Settings
@app.route('/my_account/')
@login_required
def my_account():
    return render_template("my_account.html")


# NetPop User Management Page (admin only)
@app.route('/user_management/')
@login_required
@admin_required
def user_management():
    try:
        c, conn = connection()

        data = c.execute("SELECT * FROM users")
        results = c.fetchall()

        return render_template("user_management.html", results=results)

    except Exception as e:
        return render_template("error.html", error=e)


# NetPop Endpoint Management Page (admin only)
@app.route('/endpoint/')
@login_required
@admin_required
def endpoint():
    return render_template("endpoint.html")


##### Playground ######
# jQuery Test Page
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


###### End of Playground ########

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
