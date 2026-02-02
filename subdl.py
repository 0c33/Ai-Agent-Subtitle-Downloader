import requests, time

api_key = ''

def Subtitle(title: str, IMDD_ID: str, page = 1):

    print(f'This is page: {page}\n\n\n\n')

    r = requests.get(f'https://api.subdl.com/api/v1/subtitles?imdb_id={IMDD_ID}&subs_per_page=30&languages=ar&page={page}&api_key={api_key}')

    if Check_Rate(r):
        
        time.sleep(60 * 10)
        
        return Subtitle(title, IMDD_ID, page)
    
    return r.json()

def Get_Pages(title: str, IMDD_ID: str) -> int:

    return int(Subtitle(title, IMDD_ID)['totalPages'])

def Download(subtitle_url: str):

    r = requests.get(f'https://dl.subdl.com{subtitle_url}?api_key={api_key}', stream=True)

    return r.content


def Check_Rate(req):

    if req.status_code ==429:
        return True
    
    else:
        False