from src.dbSubsManipulator import InsertTeam, IsTeamInDatabase
from src.dbSubsManipulator import LastTeamIdDb

import urllib.request, urllib.error
import json
import logging
import sys, os
import sqlite3
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

requestHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Connection': 'keep-alive'} 

# Gets the team name from the api given the teamId
# If the ID doesn't exist, it returns None
def ScrapeTeamName(teamId: int):
    requestUrl = 'https://ctftime.org/api/v1/teams/%d/' % (teamId)

    try:
        request = urllib.request.Request(requestUrl, headers=requestHeader,)
        reqResponse = urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError:
        return None

    teamInfo = json.load(reqResponse)
    teamName = teamInfo['name']
    teamIdAPI = teamInfo['id']
    assert(teamId == teamIdAPI)

    return teamName


databaseLock = threading.Lock()

def threadedFunction(teamid):
    filePath = os.path.dirname(__file__)
    relativePath = '/../db/ctfwatcherbot.db'

    try:
        dbConnection = sqlite3.connect(filePath + relativePath)
    except sqlite3.Error as error:
        logging.error("%s when connecting to database" % (error))
        return None
    global databaseLock

    if IsTeamInDatabase(dbConnection, teamid):
        print("Team %d already in db" % (teamid))
        return

    print('Scraping', teamid)
    teamName = ScrapeTeamName(teamid)

    if teamName is None:
        return

    with databaseLock:
        print("[*] Inserted team[%d]: %s" % (teamid, teamName))
        InsertTeam(dbConnection, teamid, teamName)

from time import sleep

def InsertAllTeamsIntoDatabase():
    filePath = os.path.dirname(__file__)
    relativePath = '/../db/ctfwatcherbot.db'

    try:
        dbConnection = sqlite3.connect(filePath + relativePath)
    except sqlite3.Error as error:
        logging.error("%s when connecting to database" % (error))
        return None

    nThreads = 5
    firstTeam = LastTeamIdDb(dbConnection)
    for teamid in range(firstTeam-100, 200000, nThreads):
        threads = list()
        for idx in range(0, nThreads):
            curThread = threading.Thread(target=threadedFunction,
                                        args=([teamid+idx]))
            threads.append(curThread)
            curThread.start()

        sleep(5)
        for _, thread in enumerate(threads):
            thread.join()

        print('Continuing...', teamid)
