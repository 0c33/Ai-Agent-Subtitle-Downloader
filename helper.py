import re
from classes import MultiSubtitle

DEBUG = True

def deep_get(data, path):
    node = data
    for key in path:
        node = node[key]
    return node

# def handle_multi()


def handle_subtitle_matcher(sub):
    sub = re.sub(r'[\r\n\t\xa0\u200b]+', ' ', sub).strip()
    seasonal = None

    # 1. [S2 - 11]
    m = re.search(r'\[S(\d+)\s*-\s*(\d+(?:\.\d+)?)\]', sub, re.IGNORECASE)
    if m:
        seasonal = m.group(2)

    # 2. S2 - 11 or Season 2 - 11
    if not seasonal:
        m = re.search(r'\b(?:S|Season)\s*(\d+)\s*-\s*(\d+(?:\.\d+)?)', sub, re.IGNORECASE)
        if m:
            seasonal = m.group(2)

    # 3. E/Ep/Episode (but not inside hex/hash like E26F5D9B)
    if not seasonal:
        m = re.search(r'\b(?:E|Ep|Episode)\s*(\d+(?:\.\d+)?)(?![a-zA-Z0-9])', sub, re.IGNORECASE)
        if m:
            seasonal = m.group(1).lstrip('0') or '0'

    # 4. Anime-style: " - 13 " or " - 13 End"
    if not seasonal:
        m = re.search(r' - (\d+(?:\.\d+)?)\b', sub)
        if m:
            num_str = m.group(1)
            try:
                num = float(num_str) if '.' in num_str else int(num_str)
                if 0 <= num <= 99:
                    seasonal = num_str
            except (ValueError, OverflowError):
                pass

    # 5. Fallback: - or _ + digits (more permissive)
    if not seasonal:
        m = re.search(r'[-_]\s*(\d+(?:\.\d+)?)(?=\D|$)', sub)
        if m:
            candidate = m.group(1)
            try:
                num = float(candidate) if '.' in candidate else int(candidate)
                if 0 <= num <= 99:
                    seasonal = candidate
            except (ValueError, OverflowError):
                pass

    # 6. Absolute number fallback (>99)
    absolute = None
    if not seasonal:
        m = re.search(r'(\d+(?:\.\d+)?)(?=\D|$)', sub)
        if m:
            cand = m.group(1)
            try:
                n = float(cand) if '.' in cand else int(cand)
                if n > 99:
                    absolute = cand
            except:
                pass

    return (absolute, seasonal)


def Clarify_Subtitle(subtitle):
    if (subtitle['episode_end'] or subtitle['episode_from']) != None:
        if subtitle['episode_end'] > subtitle['episode_from']:

            if DEBUG:
                print(f'This subtitle is Multi: {subtitle}\n\n')

            return MultiSubtitle(
                Episode_From=str(subtitle["episode_from"]),
                Episode_End=str(subtitle["episode_end"]),
                Full_Season=None
            )
    return None


def clean_number(number):

    if number != None:
        if number.startswith('0'):
            number = number.split('0')[-1]

            return number
    return number

def Match_Files(Episode_List, absolute_number, episode_number):

    episode_number = clean_number(episode_number)
    absolute_number = clean_number(absolute_number)

    for i in Episode_List:

        if (absolute_number == i['Episode_Absolute_Number']) or (episode_number == i['Episode_Number']): # Note maybe i need to add int()

            return i # its Matched !!