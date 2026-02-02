import requests
from helper import deep_get


headers = {'X-Api-Key': ''}
sonarr_ip = ''


def Series():

    r = requests.get(f'http://{sonarr_ip}:8989/api/v3/series', headers = headers)

    return r.json()


def Episode(series_id: str):

    r = requests.get(f'http://{sonarr_ip}:8989/api/v3/episode', params = {'seriesId': series_id}, headers = headers)

    ls = []

    for i in r.json():

        if i['hasFile'] == True:

            ls.append(i)

    return ls


def Episode_File(series_id: str, episode_id: str):

    r = requests.get(f'http://{sonarr_ip}:8989/api/v3/episodeFile/{episode_id}', params = {'seriesId': series_id}, headers = headers)

    return r.json()['path']


def Get_Series_List(param = None):

    ls = []

    for i in Series():

        if i['monitored'] and (i['statistics']['episodeFileCount'] > 0):

            if param != None:
                    
                ls.append(deep_get(i, param))

            else:

                ls.append(i)

    return ls

def Get_Series_List_v2(param = None):


    for i in Series():

        if i['monitored'] and (i['statistics']['episodeFileCount'] > 0):

            if param.lower() == (i['title']).lower():

                return i

    return None






# print(str(Get_Series_List()))