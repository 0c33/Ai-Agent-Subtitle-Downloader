from typing import Annotated, List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Command, interrupt
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
import threading, time, re, llm
from classes import State, SeriesName, SeriesEpisode, SeriesData, AltTitle, SubtitleData
from sonarr import Get_Series_List, Series, Episode, Episode_File, Get_Series_List_v2
from subdl import Subtitle, Download, Get_Pages
from files import Extract_Files, Save_File, Get_Content, Extract_File
from helper import handle_subtitle_matcher, Clarify_Subtitle, Match_Files
from IPython.display import Image, display


DEBUG = True


def Get_Series_Name(state: State) -> State:
    """Get the exact name from Sonarr Api"""

    if DEBUG:
        print(f'This is user input: {state["User_Input"]}\n\n')

    llm_worker = llm.llm.with_structured_output(SeriesName)

    prompt = f"""
    Search for this series name from sonarr database
    Requested: {state['User_Input']}
    
    {', ' + str(Get_Series_List(['title']))}"""

    response = llm_worker.invoke(prompt)


    if DEBUG:
        print(f'This is Get_Series_Name Response: {response}\n\n')

    return {"Series_Name": response['Series_Name']}


def Get_Series_Data(state: State) -> Command[Literal['Get_Series_Name', END]]:
    """Get all Series data from Sonarr Api"""

    if DEBUG:
        print(f'This is state from Get_Series_Data: {state}\n\n')

    if state['Series_Name'] is not None:
        Series_Data = Get_Series_List_v2(state['Series_Name'])

        if DEBUG:
            print(f'This is Series_Data from Get_Series_Data: {Series_Data}\n\n')
            print(f'Found Requested Series: {Series_Data['title']}\n')

        return {"Series_Data": {'Seasons': len(Series_Data['seasons']), 'Alt_Titles': [AltTitle(Title=ii['title'], Season=str(ii.get('sceneSeasonNumber') or ii.get('seasonNumber'))) for ii in Series_Data['alternateTitles']], 'Series_ID': str(Series_Data['id']), 'IMDB_ID': Series_Data['imdbId']},
                "Current_Page": 1}


    else:
        need_action = interrupt(f'Unexpected Series Name: {state["User_Input"]}: ')
        
        if need_action == 'q':
            next_node = END

        elif need_action == 'r':
            updated_user_input= input('Enter Series Name Again: ')
            next_node = 'Get_Series_Name'

        return Command(
            update = State(User_Input = updated_user_input),
            goto = next_node
        )


def Get_Series_Subtitle(state: State) -> State:
    """Get Subtitles from SubDL Api for Series"""

    if DEBUG:
        print(f'This is state from Get_Series_Subtitle: {state}\n\n')

    subtitles = Subtitle(state['Series_Name'], state['Series_Data']['IMDB_ID'], state['Current_Page'])

    subtitle_list = []

    for sub in subtitles['subtitles']:

        subtitle_entry = SubtitleData(

            Release_Name=sub['release_name'],
            Episode=str(sub['episode']), 
            Season=str(sub['season']), 
            File_Name=sub['name'], 
            URL=sub['url'], 
            Multi_Subtitle=Clarify_Subtitle(sub)
        )
    
        subtitle_list.append(subtitle_entry)


    return {
        'Subtitles': subtitle_list,
        'Current_Page': state['Current_Page'] + 1,
        'Total_Pages': subtitles['totalPages'],
        'Sub_index': 0
    }
   
def Get_Series_Episode(state: State) -> State:
    """Get Series Episodes from Sonarr Api"""

    if DEBUG:
        print(f'This is state in Get_Series_Episode: {state}')

    return {'Episodes': [SeriesEpisode(

            Episode_Number=str(i['episodeNumber']),
            Episode_Season=str(i['seasonNumber']),
            Episode_Title=i['title'],
            Episode_Absolute_Number=str(i['absoluteEpisodeNumber']),
            Episode_File=Episode_File(state['Series_Data']['Series_ID'], i['episodeFileId'])
            )   
            for i in Episode(state['Series_Data']['Series_ID'])],
            
            }


def Decider_Agent(state: State) -> Command[Literal['Handle_Unknown', 'Analyze_Multi', 'Analyze_Subtitle', 'Matcher_Agent', 'Get_Series_Subtitle', END]]:
    """Decide where to go for sub (Known and Unknown)"""

    if DEBUG:
        print(f'This is state from Decider Agent: {state}\n\n')

    updated_index = state['Sub_index']

    subtitle = state['Subtitles'][state['Sub_index'] + 15]

    if ((str(subtitle['Episode']) == 'null') and ((subtitle['Multi_Subtitle'])) == None):
        next_node = 'Handle_Unknown'

    elif subtitle['Multi_Subtitle'] != None:
        if subtitle['Multi_Subtitle']['Episode_End'] > subtitle['Multi_Subtitle']['Episode_From']:

            next_node = 'Analyze_Multi'

    elif str(subtitle['Episode']).isdigit():
        next_node = 'Analyze_Subtitle'

    else:
        next_node = 'Matcher_Agent'

    if state['Sub_index'] >= len(state['Subtitles']) - 1:
        
        if state['Current_Page'] <= state['Total_Pages']:
            next_node = 'Get_Series_Subtitle'
            updated_index = 0

        else:
            next_node = END


    else:
        updated_index = state['Sub_index'] + 1

    return Command(
        update = State(Sub_index = updated_index, Subtitle = subtitle),
        goto=next_node
    )


def Handle_Unknown(state: State) -> Command[Literal['Decider_Agent']]:
    """Recognize subtitle data after uncompressed subtitle file"""

    subtitles, content = Get_Content(Download(state['Subtitle']['URL']))

    for subtitle in subtitles:
        absolute_number, episode_number  = handle_subtitle_matcher(subtitle['File_Name'])

        if state['Series_Data']['Seasons'] == '1': # there only one season

            episode_match_file = Match_Files(state['Episodes'], absolute_number, episode_number)

            subtitle_path = Extract_File(subtitle['File_Content'], content)
            Save_File(episode_match_file, subtitle_path)

            

    #     ls.append(episode_number)

    # state['Subtitle']['Multi_Subtitle']['Episode_From'] = str(min(ls))
    # state['Subtitle']['Multi_Subtitle']['Episode_End'] = str(max(ls))








    return Command(
        update = state,
        goto='Decider_Agent'
    )


def Analyze_Multi(state: State) -> Command[Literal['Decider_Agent']]:
    """Match mutli subtitle to episodes manually"""

    # episode_matched = []

    # for episode in state['Episodes']:

    #     if state['Subtitle']['Multi_Subtitle']['Episode_End'] >= episode['Episode_Number'] >= state['Subtitle']['Multi_Subtitle']['Episode_From']:

    #         episode_matched.append(episode)

    downloaded_subtitles = Extract_Files(Download(state['Subtitle']['URL']))

    for i in downloaded_subtitles:

        print(f'This is i before crash: {i}\n\n\n')

        print(f'This is episode_matched: {state['Episodes']}\n\n\n')
        absolute_number, episode_number = handle_subtitle_matcher(i)
        print(f'This is absolute_number: {absolute_number}\n\n')
        print(f'This is episode_number: {episode_number}\n\n')
        episode_match_file = Match_Files(state['Episodes'], absolute_number, episode_number)
        
        print(f'This is episode_match_file: {episode_match_file}\n\n\n')
        Save_File(episode_match_file['Episode_File'], i)


    return Command(
        goto = 'Decider_Agent'
    )




def Analyze_Subtitle(state: State) -> Command[Literal['Decider_Agent', 'Matcher_Agent']]:
    """Trying to match episode to subtitle manually before"""

    for episode in state['Episodes']:

        if (episode['Episode_Number'] == state['Subtitle']['Episode']) and state['Subtitle']['Multi_Subtitle'] == None:

            Save_File(episode['Episode_File'], Extract_Files(Download(state['Subtitle']['URL']))[0])

            next_node = 'Decider_Agent'

        else:
            next_node = 'Matcher_Agent'

        return Command(
            update=state,
            goto=next_node
        )
            
    

def Matcher_Agent(state: State) -> Command[Literal['Decider_Agent']]:
    """LLM to match subtitle to Episode"""

    if DEBUG:
        print(f'This is state in Matcher_Agent: {state}\n\n')
        print(f'This is Subtitle before LLM Call: {state['Subtitle']}\n\n\n')

    llm_worker = llm.llm.with_structured_output(SubtitleData)

    prompt = f"""
        You are a STRICT data copier and extractor.

        You are NOT allowed to:
        - Rewrite text
        - Shorten text
        - Fix malformed text
        - Replace missing values with placeholders
        - Emit partially-filled objects

        You ONLY:
        - Copy exact values
        - Or return empty "" / null

        ABSOLUTE COPY RULE:
        If a string is copied, it MUST be byte-for-byte identical to the input.
        If you cannot copy it exactly, return "" or null instead.

        FIELD RULES:

        Release_Name:
        - MUST be copied EXACTLY from the input value.
        - If any character would be changed or removed → return "".

        File_Name:
        - Copy EXACTLY.

        URL:
        - Copy EXACTLY.
        - If missing, null, or invalid → return null.
        - NEVER invent placeholders like ":" or "/".

        Season:
        - Copy from input.
        - Convert to string only.

        Episode:
        - If input value is null, "None", 0, or missing → return "".
        - NEVER output the string "None".

        Multi_Subtitle:
        - ONLY populate if a VALID multi subtitle is detected.
        - Otherwise MUST be null.

        VALID multi subtitle requires BOTH:
        1. A real multi-episode signal exists
        2. Episode_From OR Episode_End can be explicitly extracted

        If Episode_From == "" AND Episode_End == "":
        → Multi_Subtitle MUST be null.

        Multi_Subtitle extraction rules:
        - Episode_From:
        - Must be an explicit number found in input
        - Otherwise ""
        - Episode_End:
        - Must be an explicit number found in input
        - Otherwise ""
        - Full_Season:
        - Copy EXACT boolean value from input
        - NEVER infer

        CONSISTENCY ENFORCEMENT (MANDATORY):
        - Never output empty Multi_Subtitle objects.
        - Never output placeholders.
        - Prefer null over partial data.

        OUTPUT:
        Return ONLY the structured object.
        No explanations.
        No markdown.

        =========
        INPUT:

        Subtitle Data: {state['Subtitle']}
        """



    response = llm_worker.invoke(prompt)

    print(f'This is result from Matcher Agent: {response}\n\n')

    input('Enter to continue')

    return Command(
        update = {"Matched_Result": response},
        goto = 'Decider_Agent'
    )



def main():

    graph_builder = StateGraph(State)

    graph_builder.add_node('Get_Series_Name', Get_Series_Name)
    graph_builder.add_node('Get_Series_Data', Get_Series_Data)
    graph_builder.add_node('Get_Series_Subtitle', Get_Series_Subtitle)
    graph_builder.add_node('Get_Series_Episode', Get_Series_Episode)
    graph_builder.add_node('Decider_Agent', Decider_Agent)
    graph_builder.add_node('Handle_Unknown', Handle_Unknown)
    graph_builder.add_node('Analyze_Multi', Analyze_Multi)
    graph_builder.add_node('Analyze_Subtitle', Analyze_Subtitle)
    graph_builder.add_node('Matcher_Agent', Matcher_Agent)

    graph_builder.add_edge(START, 'Get_Series_Name')
    graph_builder.add_edge('Get_Series_Name', 'Get_Series_Data')
    graph_builder.add_edge('Get_Series_Data', 'Get_Series_Subtitle')
    graph_builder.add_edge('Get_Series_Subtitle', 'Get_Series_Episode')
    graph_builder.add_edge('Get_Series_Episode', 'Decider_Agent')


    graph = graph_builder.compile()


    state = {}

    # from IPython.display import Image
    # png_bytes = graph.get_graph().draw_mermaid_png()
    # with open("langgraph_workflow.png", "wb") as f:
    #     f.write(png_bytes)

    for user_input in ['Mr Robot', 'Loki', 'The sopranos', 'pluribus', 'rick and morty', 'family guy', 'the simpsons']:

        try:

            state['User_Input'] = user_input

            for chunk in graph.stream(state, {"recursion_limit": 999}):
                    print(chunk)

        except Exception as e:
            if DEBUG:
                print(f'Exception is: {e}\n\n\n')


if __name__ == "__main__":
    main()