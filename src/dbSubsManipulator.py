import sqlite3
import logging

# Given a chatid, it returns True if a chat is subscribed, False otherwise
# In case of errors, it returns None
def IsSubscribedToAll(dbConnection: sqlite3.Connection, chatid: int):
    try:
        cursor = dbConnection.cursor()
        querySelect = 'SELECT chatid FROM subscribers WHERE chatid=?;'
        cursor.execute(querySelect, (chatid,))
        record = cursor.fetchone()
        cursor.close()

        if record is None:
            return False
        else:
            return True

    except sqlite3.Error as err:
        logging.error('Error %s when getting subscribers for chatid %d' % 
                     (err, chatid))
        return None


def InsertSubscribeToAll(dbConnection: sqlite3.Connection, chatid: int):
    try:
        cursor = dbConnection.cursor()
        queryInsert = 'INSERT INTO subscribers(chatid) VALUES (?);'
        cursor.execute(queryInsert, (chatid,))
        dbConnection.commit()
        cursor.close()

        return 0

    except sqlite3.Error as err:
        logging.error('Error %s when subbing chatid %d' %
                     (err, chatid))
        return -1


# Returns all subscribed to all teams
def GetSubscribedToAll(dbConnection: sqlite3.Connection):
    try:
        cursor = dbConnection.cursor()
        querySelect = 'SELECT chatid FROM subscribers;'
        cursor.execute(querySelect)
        record = cursor.fetchall()
        cursor.close()

        return record

    except sqlite3.Error as err:
        logging.error('Error %s when getting all subscribers' %
                     (err))
        return None

##                  ##
# Team Related Stuff #
##                  ##

# Given a chatid, it returns True if a chat is subscribed, False otherwise
# In case of errors, it returns None
def GetSubscribedTeams(dbConnection: sqlite3.Connection, chatid: int):
    try:
        cursor = dbConnection.cursor()
        querySelect = 'SELECT team FROM teamsubscribers WHERE chatid=?;'
        cursor.execute(querySelect, (chatid,))
        record = cursor.fetchall()
        cursor.close()

        return record

    except sqlite3.Error as err:
        logging.error('Error %s when getting subscribers for chatid %d' %
                     (err, chatid))
        return None

# Given a chatid, it returns True if a chat is subscribed, False otherwise
# In case of errors, it returns None
def GetSubscribedTeamsIds(dbConnection: sqlite3.Connection, chatid: int):
    try:
        cursor = dbConnection.cursor()
        querySelect = 'SELECT teamid FROM teamsubscribers WHERE chatid=?;'
        cursor.execute(querySelect, (chatid,))
        record = cursor.fetchall()
        cursor.close()

        return record

    except sqlite3.Error as err:
        logging.error('Error %s when getting subscribers for chatid %d' %
                     (err, chatid))
        return None

def SubscribeTeamId(dbConnection: sqlite3.Connection, chatid: int, teamid: int):
    try:
        cursor = dbConnection.cursor()
        queryInsert = '''
            INSERT INTO teamsubscribers(chatid, teamid)
            VALUES (?,?);
            '''
        cursor.execute(queryInsert, (chatid, teamid))
        dbConnection.commit()
        cursor.close()

        return 0

    except sqlite3.Error as err:
        logging.error('Error %s when subbing chatid %d; team %d' %
                     (err, chatid, teamid))
        return -1

def SubscribeTeam(dbConnection: sqlite3.Connection, chatid: int, teamid: int, name: str):
    try:
        cursor = dbConnection.cursor()
        queryInsert = '''
            INSERT INTO teamsubscribers(chatid, team, teamid)
            VALUES (?,?);
            '''
        cursor.execute(queryInsert, (chatid, name, teamid))
        dbConnection.commit()
        cursor.close()

        return 0

    except sqlite3.Error as err:
        logging.error('Error %s when subbing chatid %d; team %d:%s' %
                     (err, chatid, teamid, name))
        return -1


def InsertTeam(dbConnection: sqlite3.Connection, teamid: int, name: str):
    try:
        cursor = dbConnection.cursor()
        queryInsert = '''
            INSERT INTO teams(team, teamid)
            VALUES (?,?);
            '''
        cursor.execute(queryInsert, (name, teamid))
        dbConnection.commit()
        cursor.close()

        return 0

    except sqlite3.Error as err:
        logging.error('Error %s when inserting team %d:%s' %
                     (err, teamid, name))
        return -1


def IsTeamInDatabase(dbConnection: sqlite3.Connection, teamid: int):
    try:
        cursor = dbConnection.cursor()
        querySelect = 'SELECT teamid FROM teams WHERE teamid=?;'
        cursor.execute(querySelect, (teamid,))
        record = cursor.fetchone()
        cursor.close()

        if record is None:
            return False
        else:
            return True

    except sqlite3.Error as err:
        logging.error('Error %s when getting subscribers for teamid %d' % (err, teamid))
        return None

def LastTeamIdDb(dbConnection: sqlite3.Connection):
    try:
        cursor = dbConnection.cursor()
        querySelect = 'SELECT max(teamid) FROM teams;'
        cursor.execute(querySelect)
        record = cursor.fetchone()
        cursor.close()
        return record[0]

    except sqlite3.Error as err:
        logging.error('Error %s when getting lastTeamId %d' % (err))
        return None

def myFunc():
    print('fooooo')