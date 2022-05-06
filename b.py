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


def gen_good_score_list():
    conn1, cur1 = open_db()
    conn2, cur2 = open_db()

    sql = """
    select s.sname, c.cname, e.midterm, e.final
    from student s, course c, enrol e
    where s.sno = e.sno and c.cno = e.cno
    and e.midterm >= 85 and e.final >= 85;
    """

    cur1.execute(sql)
    r = cur1.fetchone()

    insert_sql = """insert into good_score_list(sname, cname, midterm, final, medium)
                    values(%s, %s, %s, %s, %s)"""

    buffer = []

    while r:
        t = (r['sname'], r['cname'], r['midterm'],
             r['final'], (r['midterm'] + r['final'])/2.0)
        buffer.append(t)

        if len(buffer) % 2 == 0:
            cur2.executemany(insert_sql, buffer)
            conn2.commit()
            buffer = []

        r = cur1.fetchone()
    if buffer:
        cur2.execute(insert_sql, buffer)
        conn2.commit()
        
    close_db(conn1, cur1)
    close_db(conn2, cur2)

if __name__ == '__main__':
    gen_good_score_list()