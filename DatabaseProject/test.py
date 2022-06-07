import time
from selenium import webdriver
import re
import pyperclip
import pymysql
import urllib.request as ur
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import naver

i = 0
AID_MAX = 500000
is_aid_checked = [False] * (AID_MAX -1)

# 크롬 웹 드라이버 경로 설정: 경로는 크롬 드라이버 있는 위치에 각자 수정
driver = webdriver.Chrome('C:\\Lisiant_Study\\study\\database_study\\DataBase_2022_1\\DatabaseProject\\Chrome_Driver\\chromedriver.exe')

# 데이터 테이블에 넣을 때 사용할 버퍼 선언
movie_data_buf = []
genre_data_buf = []
actor_data_buf = []
director_data_buf = []
movie_actor_buf = []
movie_director_buf = []
movie_photo_buf = []

def open_db():
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='jangwoo',
        password='park', db='movie_database')

    cur = conn.cursor(pymysql.cursors.DictCursor)
    return conn, cur


def close_db(conn, cur):
    cur.close()
    conn.close()

# 하나의 영화 정보 크롤링
def crawl_movie_info(mid):
    global movie_data_buf
    global genre_data_buf

    # 영화 정보 담을 리스트(튜플)
    # [mid, 영화 이름, 등급, 네티즌 평점, 네티즌 숫자, 평론가 평점, 평론가 숫자, 상영시간, 개봉일자, 이미지 링크, 줄거리]
    movie_info = []
    html = driver.page_source
    soup = bs(html, 'html.parser')
    

    # 영화 id
    movie_info.append(mid)

    # 제목
    m_title = soup.select_one('#content > div.article > div.mv_info_area > div.mv_info > h3 > a:nth-child(1)')
    movie_info.append(m_title.get_text() if m_title is not None else '')

    # 등급
    m_rate = soup.select_one('#content > div.article > div.mv_info_area > div.mv_info > dl > dd:nth-child(8) > p > a')
    movie_info.append(m_rate.get_text() if m_rate is not None else '')

    # 평점 정보
    score_area = soup.select_one('#content > div.article > div.section_group.section_group_frst > div > div > div.score_area')
    if score_area is not None:
        m_netizen_count = score_area.select_one('div.netizen_score > div > span > em')
        m_journalist_count = score_area.select_one('div.special_score > div > span > em')
        
        if m_netizen_count is not None:
            if m_netizen_count == 0: 
                movie_info += [0, 0]
            else:
                m_netizen_rate = score_area.select_one('div.netizen_score > div > div > em')
                movie_info.append(float(m_netizen_rate.get_text()) if m_netizen_rate is not None else 0)
                movie_info.append(int(re.sub(',', '', m_netizen_count.get_text())))
        
        if m_journalist_count is not None:
            if m_journalist_count == 0:
                movie_info += [0, 0]
            else:
                m_journalist_rate = score_area.select_one('div.special_score > div > div > em')
                movie_info.append(float(m_journalist_rate.get_text()) if m_journalist_rate is not None else 0)
                movie_info.append(int(m_journalist_count.get_text()))
    else:
        movie_info += [0,0,0,0]     
               
    movie_data_buf.append(movie_info)
                
                
    
    # 장르, 상영시간, 개봉일자
    info_spec_dds = soup.select('#content > div.article > div.mv_info_area > div.mv_info > dl > dd')
    scope = info_spec_dds[0].select('p>span')
    arr = [0, ''] # 상영시간, 개봉일자

    for raw_item in scope:
        links = raw_item.select('a')
        if len(links) == 0: # href 태그가 없는 경우: 상영시간
            m_playing_time = raw_item.get_text()
            arr[0] = int(m_playing_time[:-2])

        else:
            for raw_link in links:
                link = raw_link.attrs['href']
                if link.find('genre') != -1: # 장르 - (mid, gid) 형태로 저장
                    gid = int(link.split('genre=')[1])
                    genre_data_buf.append((mid, gid))
                elif link.find('open') != -1:
                    opening_date = link.split('open=')[1]
                    if len(opening_date) == 8:
                        temp = list(opening_date)
                        temp.insert(4, '-')
                        temp.insert(7, '-')
                        arr[1] = ''.join(temp)
    movie_info += arr
    
    # 기본 이미지
    image_url = soup.select_one('#content > div.article > div.mv_info_area > div.poster > a > img')
    movie_info.append(image_url.attrs['src'] if image_url is not None else '')
    
    
    # 줄거리
    raw_synopsis = soup.find("div", {"class": "story_area"})
    movie_info.append('\n'.join(raw_synopsis.text.strip().split('\n')) if raw_synopsis is not None else '')
    
    #포토
    img_element = soup.select_one('#_MainPhotoArea > div.viewer > div > img')
    img = img_element.attrs['src'] if img_element is not None else ''
    movie_photo_buf.append((mid, img))
            
      
    
def crawl_actor_director_info_from_mid(mid):
    global actor_data_buf
    global director_data_buf
    global AID_MAX
    
    # 배우
    html = driver.page_source
    soup = bs(html, 'html.parser')
    # soup = bs(ur.urlopen('https://movie.naver.com/movie/bi/mi/basic.naver?code=208857').read(), 'html.parser')
    
    actors = soup.select('#content > div.article > div.section_group.section_group_frst > div.obj_section.noline > div > div.lst_people_area.height100 > ul > li')
    actor_info = [AID_MAX, '', '', ''] #aid, ak_name, ae_name, a_image 
    movie_actor_info = [mid, AID_MAX, '', ''] # mid, aid, part, role
    
    if len(actors) == 0:
        AID_MAX += 1
        actor_data_buf.append([AID_MAX, '', '', ''])
        movie_actor_buf.append([mid, AID_MAX, '', ''])
        
    for actor in actors: # 배우 탭이 존재하는 경우
        ak_name = actor.select_one('div > a')
        if ak_name is not None:
            
            if ak_name.attrs['href'].find('code=') != -1:
                aid = int(ak_name.attrs['href'].split('code=')[1])
                actor_info[0] = aid
                if is_aid_checked[aid]: # 같은 배우가 다른 영화에 나온 경우(actor테이블에 이미 튜플 존재)
                    movie_actor_info[1] = aid   # movie_actor 테이블에 저장할 값을 업데이트
                    continue
                else:
                    is_aid_checked[aid] = True
                    movie_actor_info[1] = aid
                
            actor_info[1] = ak_name.text
            
        ae_name = actor.select_one('div > em')
        actor_info[2] = ae_name.text if ae_name is not None else ''

        a_image = actor.select_one('p > a > img')
        actor_info[3] = a_image.attrs['src'] if a_image is not None else ''
        actor_data_buf.append(tuple(actor_info))       
        actor_info = [AID_MAX, '', '', '']
        
        part = actor.select_one('div > div > p > em')
        movie_actor_info[2] = part.text if part is not None else ''
        role = actor.select_one('div > div > p > span')
        movie_actor_info[3] = role.text if role is not None else ''
        
        
        movie_actor_buf.append(tuple(movie_actor_info))  
        movie_actor_info = [mid, AID_MAX, '', '']
        
    
    directors = soup.select('#content > div.article > div.section_group.section_group_frst > div.obj_section > div > div.dir_obj')
    dir_info = [AID_MAX, '', '', ''] #did, dk_name, de_name, d_image 
    movie_dir_info = [mid, AID_MAX] # mid, did
    
    if len(directors) == 0:
        AID_MAX += 1
        director_data_buf.append([AID_MAX, '', '', ''])
        movie_director_buf.append([mid, AID_MAX])
    
    for director in directors:
        d_link = director.select_one('p > a')
        if d_link is not None:
            
            if d_link.attrs['href'].find('code=') != -1:
                did = int(d_link.attrs['href'].split('code=')[1])
                dir_info[0] = did
                if is_aid_checked[did]:
                    movie_dir_info[1] = did
                    continue
                is_aid_checked[did] = True
                movie_dir_info[1] = did
            
            
        dk_name = director.select_one('div > a')
        dir_info[1] = dk_name.text if dk_name is not None else ''
        
        de_name = director.select_one('div > em')
        dir_info[2] = de_name.text if de_name is not None else ''
        
        d_image = director.select_one('p > a > img')
        dir_info[3] = d_image.attrs['src'] if d_image is not None else ''
        
        director_data_buf.append(tuple(dir_info))
        dir_info = [AID_MAX, '', '', ''] 
        
        movie_director_buf.append(tuple(movie_dir_info))
        movie_dir_info = [mid, AID_MAX] 
        

        
def parse_mid_from_url(url):
    tmp = url.split('code=')
    return int(tmp[1])
    
def fault_handler(mid, e, conn, cur, fault_location):
    global i
    i += 1
    print(i, mid, e, fault_location)
    

    if fault_location == 1:
        movie_data_buf.clear()
    elif fault_location == 2:
        actor_data_buf.clear()
    elif fault_location == 3:
        director_data_buf.clear()
    elif fault_location == 4:
        movie_actor_buf.clear()
    elif fault_location == 5:
        movie_director_buf.clear()
    elif fault_location == 6:
        genre_data_buf.clear()
    elif fault_location == 7:
        movie_photo_buf.clear()
    insert_into_table(mid)
        



def fault_handler_main(mid, e, conn, cur):
    print("fault at main")
       
    

def insert_into_table(mid):
    global movie_data_buf
    global genre_data_buf
    global actor_data_buf
    global director_data_buf
    global movie_actor_buf
    global movie_director_buf
    global movie_photo_buf
    
    conn, cur = open_db()
    
    insert_movie(mid, conn, cur)
    insert_actor(mid, conn, cur)
    insert_director(mid, conn, cur)
    insert_movie_actor(mid, conn, cur)
    insert_movie_director(mid, conn, cur)
    insert_movie_genre(mid, conn, cur)
    insert_movie_photo(mid, conn, cur)
        
    close_db(conn, cur)
    
    
def insert_movie(mid, conn, cur):
    if len(movie_data_buf) == 0:
        return
    
    insert_sql_movie = """
    insert ignore into movie (mid, m_name, m_rate, m_netizen_rate, m_netizen_count, m_journalist_score, m_journalist_count, m_playing_time, m_opening_date, m_image, m_synopsis)
    values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    try:
        cur.executemany(insert_sql_movie, movie_data_buf)
        conn.commit()
        movie_data_buf.clear()
    except Exception as e:
        fault_handler(mid, e, conn, cur, 1)
    
def insert_actor(mid, conn, cur):
    if len(actor_data_buf) == 0:
        return
    insert_sql_actor = """
    insert ignore into actor (aid, ak_name, ae_name, a_image)
    values(%s, %s, %s, %s)
    """

    try:
        cur.executemany(insert_sql_actor, actor_data_buf)
        conn.commit()
        actor_data_buf.clear()
        
    except Exception as e:
        print(actor_data_buf)
        fault_handler(mid, e, conn, cur, 2)
         
def insert_director(mid, conn, cur):
    if len(director_data_buf) == 0:
        return
    insert_sql_director = """
    insert ignore into director (did, dk_name, de_name, d_image)
    values(%s, %s, %s, %s)
    """

    try:
        cur.executemany(insert_sql_director, director_data_buf)
        conn.commit()
        director_data_buf.clear()
        
    except Exception as e:
        fault_handler(mid, e, conn, cur, 3)
         
def insert_movie_actor(mid, conn, cur):
    
    if len(movie_actor_buf) == 0:
        return
    
    insert_sql_movie_actor = """
    insert ignore into movie_actor (mid, aid, part, role)
    values(%s, %s, %s, %s)
    """
    
    try:
        cur.executemany(insert_sql_movie_actor, movie_actor_buf)
        conn.commit()
        movie_actor_buf.clear()
    except Exception as e:
        print("movie_actor_buf", movie_actor_buf)
        fault_handler(mid, e, conn, cur, 4)
           
def insert_movie_director(mid, conn, cur):
    
    if len(movie_director_buf) == 0:
        return
    
    insert_sql_movie_director = """
    insert ignore into movie_director (mid, did)
    values(%s, %s)
    """
    
    try:
        cur.executemany(insert_sql_movie_director, movie_director_buf)
        conn.commit()
        movie_director_buf.clear()
        
    except Exception as e:
        fault_handler(mid, e, conn, cur, 5)
    
def insert_movie_genre(mid, conn, cur):
    
    if len(genre_data_buf) == 0:
        return
    insert_sql_movie_genre = """
    insert ignore into movie_genre(mid, gid)
    values(%s, %s)
    """
    

    try: 
        cur.executemany(insert_sql_movie_genre, genre_data_buf)
        conn.commit()
        genre_data_buf.clear()
        
    except Exception as e:
        fault_handler(mid, e, conn, cur, 6)

def insert_movie_photo(mid, conn, cur):
    if len(movie_photo_buf) == 0:
        return
    insert_sql_movie_photo = """
    insert ignore into movie_photo (mid, mp_photo)
    values(%s, %s)
    """
       
    try: 
        cur.executemany(insert_sql_movie_photo, movie_photo_buf)
        conn.commit()
        movie_photo_buf.clear()
        
    except Exception as e:
        fault_handler(mid, e, conn, cur, 7)

def login():
    login_btn = driver.find_element(by=By.CSS_SELECTOR, value='#gnb_login_button')
    login_btn.click()
    
    
    naver_id = naver.naver_id
    naver_pw = naver.naver_pw
    
    element_id = driver.find_element_by_id('id')
    element_id.click()
    pyperclip.copy(naver_id)
    element_id.send_keys(Keys.CONTROL +'v')
    time.sleep(1)
    
    element_pw = driver.find_element_by_id('pw')
    element_pw.click()
    element_pw.click()
    pyperclip.copy(naver_pw)
    element_pw.send_keys(Keys.CONTROL + 'v')
    time.sleep(1)

    
    driver.find_element_by_id('log.login').click()
    time.sleep(1)
    driver.find_element_by_id('new.save').click()
    time.sleep(1)
     

    
def main(): 
    
    conn, cur = open_db()
    
    # 크롬을 통해 네이버 영화 디렉토리 페이지에 접속
    url = 'https://movie.naver.com/movie/sdb/browsing/bmovie_open.naver'
    driver.get(url)
    login()
    year_directory = driver.find_elements(by=By.XPATH, value='//*[@id="old_content"]/table/tbody/tr/td/a')
    # 2023~2012년도 영화 수집: 대략 10000
    # 2020.06.07 18:51 현재 2019년도까지 수집 완료. (2674개 영화) 
    for current_year in year_directory[5:11]: 
        
        current_year.send_keys(Keys.CONTROL + '\n')
        driver.switch_to.window(driver.window_handles[1])

        while True:
            movie_directory = driver.find_elements(by=By.XPATH, value='//*[@id="old_content"]/ul/li')
            
            for current_movie in movie_directory:
                movie_info_link = current_movie.find_element(by=By.CSS_SELECTOR, value='a')
                movie_info_link.send_keys(Keys.CONTROL + '\n')
                driver.switch_to.window(driver.window_handles[2])
            
                
                try:
                # 영화 상세정보 페이지에서 영화 크롤링
                    mid = parse_mid_from_url(driver.current_url)
                    crawl_movie_info(mid)
                
                # 배우/제작진 페이지로 이동 후 크롤링 //*[@id="movieEndTabMenu"]/li[2]
                    actor_link = driver.find_element(by =By.XPATH, value='//*[@id="movieEndTabMenu"]/li[2]/a')
                    actor_link.send_keys(Keys.CONTROL + '\n')
                    driver.switch_to.window(driver.window_handles[3])
                    crawl_actor_director_info_from_mid(mid)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[2])
                    
                    insert_into_table(mid)
                    
                
                except Exception as e:
                    fault_handler_main(parse_mid_from_url(driver.current_url), e, conn, cur)
                
                
            
                driver.close()
                driver.switch_to.window(driver.window_handles[1])
                
              

            if not driver.find_elements(by=By.CSS_SELECTOR, value='#old_content > div.pagenavigation > table > tbody > tr > td.next > a'):
                break
            else:
                driver.find_element(by=By.CSS_SELECTOR, value='#old_content > div.pagenavigation > table > tbody > tr > td.next > a').click()

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
    close_db(conn,cur)
    driver.quit()


if __name__ == '__main__':
    main()

