import pymysql

def connection():
    conn = pymysql.connect(host = "localhost",
                            user = "ashoover",
                            passwd = "password",
                            db = "netpop")

    c = conn.cursor()

    return c, conn