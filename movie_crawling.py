import urllib.request as ur
from bs4 import BeautifulSoup as bs

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
enter_date = []

soup = bs(ur.urlopen('https://movie.naver.com/movie/running/current.naver').read(), 'html.parser')


lst = soup.select('#content > div.article > div:nth-child(1) > div.lst_wrap > ul > li')


def append_list(arr, selector):

    if selector is not None:
        arr.append(selector.get_text())
    else:
        arr.append("not exists")

        

for item in lst:
    tit = item.select_one('dl > dt > a')
    append_list(title, tit)

    grade = item.select_one('dl > dt > span')
    append_list(movie_rate, grade)
    
    n_rate = item.select_one('dl > dd > dl > dd:nth-child(2) > div > a > span.num')
    append_list(netizen_rate, n_rate)
    
    j_rate = item.select_one('dl > dd > dl > dd:nth-child(4) > div > a > span.num')
    append_list(journalist_score, j_rate)
    
    n_count = item.select_one('dl > dd.star > dl > dd:nth-child(2) > div > a > span.num2 > em')
    append_list(netizen_count, n_count)

    j_count = item.select_one('dl > dd.star > dl > dd:nth-child(4) > div > a > span.num2 > em')
    append_list(journalist_count, j_count)
    
    genres = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span.link_txt > a')
    temp = []
    for genre in genres:
        temp.append(genre.get_text())
    if len(temp) == 1:
        scope.append(temp[0])
    else:
        scope.append(', '.join(temp))
    
    split1 = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span:nth-child(2)')
    for m_time in split1:
        playing_time.append(str(m_time.next_sibling).strip())
    
    
    split2 = item.select('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span:nth-child(3)')
    for raw_date in split2:
        date = str(raw_date.next_sibling).strip()[:10].split('.')
        opening_date.append('-'.join(date))


    director_selector = item.select_one('dl > dd:nth-child(3) > dl > dd:nth-child(4) > span > a')
    append_list(director, director_selector)
    
    img_ref = item.select_one('div > a > img')
    if img_ref is not None:
        image.append(img_ref.get("src"))
    else:
        image.append("no image")
        
