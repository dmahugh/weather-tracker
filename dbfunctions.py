"""helper functions for working with the Cloud SQL database
"""
import pymysql

import defaults


def db_connection(*, host=None, user=None, pwd=None, database=None):
    """Creates and returns a pymysql connection object.

    Args:
        host: host URL
        user: database user name
        pwd: password for user
        database: name of the database

        If any of the above arguments are omitted, default values from
        defaults.py are used.

    Returns:
        A pymysql connection object for the specified database/user.
    """
    connection = pymysql.connect(
        host=defaults.HOST if host is None else host,
        user=defaults.USER if user is None else user,
        password=defaults.PWD if pwd is None else pwd,
        database=defaults.DATABASE if database is None else database,
    )
    return connection


def drop_table(cnxn, tablename):
    """Drops a table, regardless of whether it exists.
    
    Args:
        cnxn: a pymysql connection object
        tablename: the table to be dropped

    Returns:
        A boolean value indicating whether the table existed.
    """
    existed = True
    cursor = cnxn.cursor()
    try:
        cursor.execute(f"DROP TABLE {tablename}")
    except pymysql.err.InternalError:
        existed = False
    return existed


def initialize_database():
    """Initializes the wtracker database, by creating the Forecast and
    Location tables, then adding default locations to Location table.

    WARNING: DELETE ANY EXISTING DATA IN THESE TABLES.

    Args:
        none

    Returns:
        none
    """
    # for safety in case defaults change, explicitly specify the database
    cnxn = db_connection(database="forecasts")

    # drop tables
    for table in ["Forecast", "Location"]:
        if drop_table(cnxn, tablename=table):
            print(f"{table} table existed, has been dropped")
        else:
            print(f"{table} table did not exist")

    cursor = cnxn.cursor()

    # create the tables
    cursor.execute(
        "CREATE TABLE Forecast (ForecastID INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(ForecastID), Epoch INT, ForecastDT CHAR(20), City VARCHAR(40), LocationID INT, Conditions VARCHAR(40), Temp INT, Humidity INT, Cloudy INT, Wind CHAR(7), IconURL VARCHAR(50))"
    )
    cursor.execute(
        "CREATE TABLE Location (LocationID INT, PRIMARY KEY(LocationID), City VARCHAR(40), Country CHAR(2), Tracked BOOLEAN)"
    )

    # populate location table
    for owm_id, city, country in [
        [5_809_844, "Seattle", "US"],
        [2_643_741, "London", "UK"],
        [2_965_140, "Cork", "IE"],
        [2_964_077, "Glenbeigh", "IE"],
        [3_128_832, "Madrid", "ES"],
        [6_454_924, "Nice", "FR"],
    ]:
        cursor.execute(
            f'INSERT INTO Location (LocationID, City, Country, Tracked) values({owm_id}, "{city}", "{country}", TRUE)'
        )

    # print summary
    print_rows(cnxn, f"DESCRIBE Forecast")
    print_rows(cnxn, f"DESCRIBE Location")
    print_rows(cnxn, f"SELECT * FROM Location")

    cnxn.close()


def print_rows(cnxn, sql):
    """A convenience helper function that runs a SQL command and prints all
    returned rows to the console.

    Args:
        cnxn: a pymysql connection object
        sql: the SQL command to be executed

    Returns:
        none
    """
    print(sql.center(70, "-"))
    with cnxn:
        cur = cnxn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                print(row)
        except pymysql.err.ProgrammingError:
            print(f"SQL command failed: {sql}")
