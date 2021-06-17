import sqlite3
from random import randint
import pytest

# Hacky thing to import
#import sys, os
#sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from src import dbSubsManipulator
import db.dbCreator

def initDatabase(dbConnection: sqlite3.Connection):
    db.dbCreator.CreateTables(dbConnection)

def test_subscribingToAll():
    validChatId = randint(-10000000000, 10000000000)
    unsubbedChatId = 0
    
    try:
        dbConn = sqlite3.connect(':memory:')

        # Initialize database
        initDatabase(dbConn)

    except sqlite3.Error:
        assert False, "Failed to connect to database"

    # Check database initialization, if nothing unexpected happened
    isSubbed = dbSubsManipulator.IsSubscribedToAll(dbConn,
                                                   validChatId)
    assert isSubbed == False, "Is Subscribed returning true when it shouldn't"

    # Test both the case of an unsubbed and subbed teams
    err = dbSubsManipulator.InsertSubscribeToAll(dbConn, validChatId)
    assert err != -1, "Error when inserting subscription to all"
    isSubbed1 = dbSubsManipulator.IsSubscribedToAll(dbConn,
                                                   validChatId)
    isSubbed2 = dbSubsManipulator.IsSubscribedToAll(dbConn,
                                                   unsubbedChatId)
    assert isSubbed1 is True and isSubbed2 is False, "Failed subscription"

    # Test basic GetSubbedToAll
    subbedList = dbSubsManipulator.GetSubscribedToAll(dbConn)
    assert len(subbedList) == 1, "Wrong number of subbed teams"

    # Insert new team and test it
    err = dbSubsManipulator.InsertSubscribeToAll(dbConn, unsubbedChatId)
    assert err != -1, "Error when inserting subscription to all"
    subbedList2 = dbSubsManipulator.GetSubscribedToAll(dbConn)
    assert subbedList != subbedList2, "Subbed lists are supposed to be different"
    assert ((subbedList2[0][0] == validChatId and subbedList2[1][0] == unsubbedChatId)
            or (subbedList2[0][0] == unsubbedChatId and subbedList2[1][0] == validChatId))
    assert len(subbedList2) == 2


def test_subbedTeamIds():
    validChatId = randint(-10000000000, 10000000000)
    unsubbedChatId = 0

    validTeamId1 = randint(0, 150000)
    validTeamId2 = randint(0, 150000)

    try:
        dbConn = sqlite3.connect(':memory:')

        # Initialize database
        initDatabase(dbConn)

    except sqlite3.Error:
        assert False, "Failed to connect to database"

    # Check database initialization, if nothing unexpected happened
    subbedTeams = dbSubsManipulator.GetSubscribedTeamsIds(dbConn,
                                                    validChatId)
    assert len(subbedTeams) == 0, "No teams should be subbed"

    # Test both the case of an unsubbed and subbed teams
    err = dbSubsManipulator.SubscribeTeamId(dbConn,
                                            validChatId, validTeamId1)
    assert err != -1, "Error when inserting subscribing team"
    subList1 = dbSubsManipulator.GetSubscribedTeamsIds(dbConn,
                                                   validChatId)
    subList2 = dbSubsManipulator.GetSubscribedTeamsIds(dbConn,
                                                   unsubbedChatId)
    assert len(subList1) == 1 and len(subList2) == 0, "Failed team subscription check"
    assert subList1[0][0] == validTeamId1, "Team id not subbed"

    # Insert new team and test it
    err = dbSubsManipulator.SubscribeTeamId(dbConn, validChatId, validTeamId2)
    assert err != -1, "Error when inserting subscription to all"
    updatedSubbed = dbSubsManipulator.GetSubscribedTeamsIds(dbConn, validChatId)
    assert subbedTeams != updatedSubbed, "Subbed lists are supposed to be different"
    assert ((updatedSubbed[0][0] == validTeamId1 and updatedSubbed[1][0] == validTeamId2)
            or (updatedSubbed[0][0] == validTeamId2 and updatedSubbed[1][0] == validTeamId1))
    assert len(updatedSubbed) == 2