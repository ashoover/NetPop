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