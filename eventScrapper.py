from requests import get
from bs4 import BeautifulSoup
from collections import defaultdict

# Makes a request to a url and returns a beautifulSoup object
def makeRequest(url):
    reqHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}

    try:
        req = get(url, headers=reqHeader, timeout = 5)
    except:
        print("Request to url {} failed!".format(url))

    html = BeautifulSoup(req.content, 'html.parser')

    return html

# Returns the list of participating teams in a subscribers list
def getEventParticipants(eventId):
    url = 'https://ctftime.org/event/{}'.format(eventId)

    html = makeRequest(url)
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

def getRating(eventId):
    url = 'https://ctftime.org/event/{}'.format(eventId)
    html = makeRequest(url)

    # Gets the team list 
    teamList = html.findAll('tr')[1:]

    scoreboard = []
    for team in teamList:
        teamInfo = team.findAll('td')
        place = teamInfo[1].text
        teamName = teamInfo[2].text
        #points = teamInfo[3].text
        rating = teamInfo[4].text

        scoreboard.append([teamName, place, rating])

    return scoreboard

