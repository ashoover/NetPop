# NetPop

Requirements : 
  -  blinker==1.4
  -  Click==7.0
  -  Flask==1.0.2
  -  Flask-Executor==0.8.3
  -  Flask-Mail==0.9.1
  -  Flask-Session==0.3.1
  -  Flask-WTF==0.14.2
  -  itsdangerous==1.1.0
  -  Jinja2==2.10
  -  MarkupSafe==1.1.0
  -  passlib==1.7.1
  -  PyMySQL==0.9.3
  -  Werkzeug==0.14.1
  -  WTForms==2.2.1
  -  ping3==1.4.1

MySQL DB:
Table info in db_setup.sql.  I probably wouldn't use that yet as it's not up to date.

Ranks :
 - 0  Disabled Account
 - 1  Guest (No-Access - to be used later)
 - 2  Monitor - Monitor Page Access Only (Default)
 - 3  Administrator (Settings Page Access BUT must be set manually in the db)

 To Run : ``` python netpop.py ```

 Demo Site : https://dd-util02.duckdns.org

 