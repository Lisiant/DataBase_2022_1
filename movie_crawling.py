import re
import pymysql
import urllib.request as ur
from bs4 import BeautifulSoup as bs

movie = [[] for _ in range(11)]
title = []
movie_rate = []
netizen_rate = []
netizen_count = []
journalist_score = []
journalist_count = []
scope = []
playing_time = []
opening_date = []
director = []
image = []


def open_db():
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='jangwoo',
        password='park', db='movie')

    cur = conn.cursor(pymysql.cursors.DictCursor)
    return conn, cur


def close_db(conn, cur):
    cur.close()
    conn.close()


def append_list_one(arr, selector):
    if selector is not None:
        arr.append(selector.get_text())
    else:
        arr.append("null")


def append_list_mul(arr, selector):
    temp = []
    for item in selector:
        temp.append(item.get_text())
        if len(temp) == 1:
            arr.append(temp[0])
        else:
            arr.append(', '.join(temp))


def append_img(arr, selector):
    if selector is not None:
        arr.append(selector.get("src"))
    else:
        arr.append(None)
        
        
def append_playing_time(arr, selector):
    for time in selector:
        arr.append(str(time.next_sibling).strip())
        
def append_date(arr, selector):
    for raw_date in selector:
        date = str(raw_date.next_sibling).strip()[:10].split('.')
        arr.append('-'.join(date))

def crawl_data(arr):
    for item in arr:
        sel_title = item.select_one('dl > dt > a')
        sel_rate = item.select_one('dl > dt > span')
        n_rate = item.select_one('dl > dd > dl > dd:nth-child(2) > div > a > span.num')
        j_rate = item.select_one('dl > dd > dl > dd:nth-child(4) > div > a > span.num')
        n_count = item.select_one('dl > dd.star > dl > dd:nth-child(2) > div > a > span.num2 > em')
        j_count = item.select_one('dl > dd.star > dl > dd:nth-child(4) > div > a > span.num2 > em')
        sel_scope = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span.link_txt > a')
        sel_time = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span:nth-child(2)')
        sel_date = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span:nth-child(3)')
        sel_dir = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(4) > span > a')
        sel_img = item.select_one('div > a > img')
        

        append_list_one(title, sel_title)
        append_list_one(movie_rate, sel_rate)
        append_list_one(netizen_rate, n_rate)
        append_list_one(journalist_score, j_rate)
        append_list_one(netizen_count, n_count)
        append_list_one(journalist_count, j_count)
        append_list_mul(scope, sel_scope)
        append_list_mul(director, sel_dir)
        append_img(image, sel_img)
        append_playing_time(playing_time, sel_time)
        append_date(opening_date, sel_date)


    movie[0] = title

    for rate in movie_rate:
        if rate == 'null':
            movie[1].append(None)
        else:
            movie[1].append(rate)

    for rating in netizen_rate:
        if rating == 'null':
            movie[2].append(0.00)
        else:
            movie[2].append(float(rating))

    for count in netizen_count:
        if count == 'null':
            movie[3].append(0)
        else:
            movie[3].append(int(re.sub(',', '', count)))

    for rating in journalist_score:
        if rating == 'null':
            movie[4].append(0.00)
        else:
            movie[4].append(float(rating))

    for count in journalist_count:
        if count == 'null':
            movie[5].append(0)
        else:
            movie[5].append(int(count))

    movie[6] = scope

    for time in playing_time:
        if time == 'null':
            movie[7].append(0)
        else:
            movie[7].append(int(re.sub('분', '', time)))

    movie[8] = opening_date
    movie[9] = director
    movie[10] = image


def insert_into_table():
    conn, cur = open_db()

    insert_sql = """
    insert into movie(title, movie_rate, netizen_rate, netizen_count, journalist_score, journalist_count, scope, playing_time, opening_date, director, image)
    values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    buf = []
    temp = []

    for i in range(len(movie[0])):
        for j in range(11):
            temp.append(movie[j][i])

        buf.append(tuple(temp))
        temp = []
        if len(buf) % 2 == 0:
            cur.executemany(insert_sql, buf)
            conn.commit()
            buf = []

    if buf:
        cur.executemany(insert_sql, buf)
        conn.commit()

    close_db(conn, cur)



def execute(sql):
    conn, curs = open_db()
    curs.execute(sql)
    close_db(curs, conn)


if __name__ == '__main__':

    soup = bs(ur.urlopen('https://movie.naver.com/movie/running/current.naver').read(), 'html.parser')
    data = soup.select('#content > div.article > div:nth-child(1) > div.lst_wrap > ul > li')

    crawl_data(data)

    drop_table_sql = """ drop table movie;"""
    create_table_sql = """create table movie(
    title varchar(100) primary key,
	movie_rate varchar(20) default null,
    netizen_rate float default 0.00,
    netizen_count int default 0,
    journalist_score float default 0.00,
    journalist_count int default 0,
    scope varchar(100),
    playing_time int,
    opening_date datetime default now(),
    director varchar(100),
    image varchar(1000),
    enter_date datetime default now()   
    );"""
    
    execute(drop_table_sql)
    execute(create_table_sql)
    insert_into_table()