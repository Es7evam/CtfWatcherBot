from requests import get
from bs4 import BeautifulSoup
from collections import defaultdict

# Returns the list of participating teams in a subscribers list
def getEventParticipants(eventId):
    reqHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}

    url = 'https://ctftime.org/event/{}'.format(eventId)
    req = get(url, headers=reqHeader, timeout=5)

    # HTML Parsing
    html = BeautifulSoup(req.content, 'html.parser')
    teams = html.findAll('td')

    # Searching for the teams in the event
    # Using the name only, could implement using team id eventually
    participants = []
    for team in teams:
        teamName = team.find('a').text.lower()
        participants.append(teamName)
        
    return participants

def listToDict(LTeamSubscribers):
    teamDict = defaultdict(list)
    for k, v in LTeamSubscribers.items():
        teamDict[int(k)] = v
    
    return teamDict

