import sqlite3
import os


def CreateTables(dbConnection):
    queryCreateSubscribers = '''
        CREATE TABLE subscribers (
            chatid INTEGER PRIMARY KEY
        );
    '''

    queryCreateTeams = '''
        CREATE TABLE teams (
            teamid INTEGER PRIMARY KEY,
            team TEXT
        );
    '''

    queryCreateTeamSubscribers = '''
        CREATE TABLE teamsubscribers (
            chatid INTEGER,
            team TEXT, 
            teamid INTEGER,
            FOREIGN KEY(chatid) REFERENCES subscribers(chatid)
            FOREIGN KEY(teamid) REFERENCES teams(teamid)
            PRIMARY KEY(chatid, teamid)
        );
    '''

    queryCreateCtfInfo = '''
        CREATE TABLE ctfinfo (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url TEXT,
            start TEXT,
            finish TEXT,
            weight REAL,
            format TEXT,
            description TEXT,
            prizes TEXT
        );
    '''

    queryCreateCtfWarning = '''
        CREATE TABLE ctfwarning (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
            dayWarned INTEGER,
            hourWarned INTEGER,
            start TEXT,
            duration INTEGER
        );
    '''

    try:
        cursor = dbConnection.cursor()
        cursor.execute(queryCreateCtfInfo)
        cursor.execute(queryCreateCtfWarning)
        cursor.execute(queryCreateSubscribers)
        cursor.execute(queryCreateTeams)
        cursor.execute(queryCreateTeamSubscribers)
        dbConnection.commit()
        print("Tables created :D")
        cursor.close()

    except sqlite3.Error as error:
        print("Error while creating sqlite table", error)


def DeleteTables(dbConnection):
    try:
        cursor = dbConnection.cursor()
        cursor.execute('DROP TABLE ctfwarning;')
        cursor.execute('DROP TABLE ctfinfo;')
        cursor.execute('DROP TABLE teamsubscribers;')
        cursor.execute('DROP TABLE teams;')
        cursor.execute('DROP TABLE subscribers;')
        dbConnection.commit()
        print("Tables deleted :(")
        cursor.close()

    except sqlite3.Error as error:
        print("Error while deleting tables", error)


def run():
    try:
        filePath = os.path.dirname(__file__)
        dbConnection = sqlite3.connect(filePath + '/ctfwatcherbot.db')
        print("Successfully connected to ctfwatcherbot database")

        # DeleteTables(dbConnection)
        CreateTables(dbConnection)
    except sqlite3.Error as error:
        print("Error while connecting to db", error)
    finally:
        if (dbConnection):
            dbConnection.close()
            print("Database connection was closed successfully")

if __name__ == "__main__":
    run()