from dbconnect import connection

def total_endpoints():
    try:
        c, conn = connection()
        c.execute("SELECT count(*) FROM endpoints;")

        results = c.fetchone()
        results = results[0]

        c.close()
        conn.close()

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