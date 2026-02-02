from typing import List, Optional, TypedDict, Literal

class AltTitle(TypedDict):

    Title: str
    Season: str

class SeriesEpisode(TypedDict):

    Episode_Number: str
    Episode_Season: str
    Episode_Title: str
    Episode_Absolute_Number: str
    Episode_File: str

class SeriesData(TypedDict):

    Seasons: int
    Alt_Titles: List[AltTitle]
    Series_ID: str
    IMDb_ID: str

class MultiSubtitle(TypedDict):

    Episode_From: str
    Episode_End: str
    Full_Season: bool | None

class SubtitleData(TypedDict):

    Release_Name: str
    Episode: str
    Season: str
    File_Name: str
    URL: str | None

    Multi_Subtitle: MultiSubtitle | None


class State(TypedDict):

    # user inputs
    User_Input: str

    # Series Data
    Series_Name: str
    Series_Data: SeriesData
    Episodes: List[SeriesEpisode]

    # Subtitle Data
    Subtitles: List[SubtitleData]
    Subtitle_File: str

    # SubDL Api
    Current_Page: int
    Total_Pages: int

    # Decider - Temp Data
    Subtitle: SubtitleData

    # LLM
    Sub_index: int


# These are just helpers

class SeriesName(TypedDict):
    Series_Name: str


class Decision(TypedDict):
    Result: bool