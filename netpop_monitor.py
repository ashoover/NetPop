import requests
from dbconnect import connection
import time
import socket

# Random Variables
time_now = time.strftime("%H:%M %m-%d-%Y")

endpoints = "db connection minus disabled endpoints"

def isOpen(ip,port):
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   try:
      s.connect((ip, int(port)))
      s.shutdown(2)
      return True
   except:
      return False

for endpoint in endpoints:
    pass