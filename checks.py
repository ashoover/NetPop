from dbconnect import connection

def NP_DBStatus():
    try :
        conn = connection()
        status = "OK"

    except Exception:
        status = "Problem" 

    return status