import pymysql


def open_db():

    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='mys@Clive.P1350!', db='university')

    cur = conn.cursor(pymysql.cursors.DictCursor)
    return conn, cur


def close_db(conn, cur):
    cur.close()
    conn.close()


def simple_select():
    conn, cur = open_db()
    sql = """
    select *
    from student;
    """

    cur.execute(sql)
    r = cur.fetchone()
    
    while r:
        print(r['sname'], r['dept'])
        r = cur.fetchone()
    close_db(conn, cur)


if __name__ == '__main__':
    simple_select()
