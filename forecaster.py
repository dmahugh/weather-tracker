"""weather tracker app

Before running this code, open a command window and run this command to launch the proxy:
cloud_sql_proxy -instances=weather-tracker-238317:us-west1:wtracker=tcp:3306
"""
import datetime

from dbfunctions import db_connection


def get_forecasts():
    """Queries the database to return the forecasts for each tracked location.

    Args:
        none (looks to the Location.Tracked column to determine which locations
        are being tracked)

    Returns:
        A dict mapping each tracked location's city name to a forecast stored
        as a dictionary. For example:

        {'London': {'timestamp': '2019-04-25 09:00:00',
                    'conditions': 'Rain',
                    'temperature': 52,
                    'humidity': 72,
                    'perc_cloudy': 100,
                    'wind': '4 S'}
    """
    forecasts = {}
    connection = db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT LocationID, City FROM Location WHERE Tracked=TRUE")
    rows = cursor.fetchall()
    for owm_id, city in rows:
        forecasts[city] = get_forecast(cursor, owm_id)
    connection.close()
    return forecasts


def get_forecast(cursor, location):
    """Gets the forecast for a location and returns it as a dictionary.

    The returned forecast is either the first forecast after the current UTC
    time, or the most recent forecast we have in the database if none are
    after the current date/time.

    Args:
        cursor: a cursor for a pymysql connection object
        location: a valid OpenWeatherMap location ID value (int)

    Returns:
        A dict containing the forecast. For example:

        {'timestamp': '2019-04-25 09:00:00',
         'conditions': 'Rain',
         'temperature': 52,
         'humidity': 72,
         'perc_cloudy': 100,
         'wind': '4 S'}
    """
    cursor.execute(f"SELECT * FROM Forecast WHERE LocationID={location} ORDER BY Epoch")
    rows = cursor.fetchall()
    current_utc_epoch = datetime.datetime.utcnow().timestamp()
    for row in rows:
        forecast = row
        epoch = forecast[1]
        if epoch > current_utc_epoch:
            break
    return {
        "timestamp": forecast[2],
        "conditions": forecast[5],
        "temperature": forecast[6],
        "humidity": forecast[7],
        "perc_cloudy": forecast[8],
        "wind": forecast[9],
    }


def main():
    """Prints current forecasts for all tracked locations to the console.

    Args:
        none

    Returns:
        none
    """
    forecasts = get_forecasts()
    print(
        "\ndate/time          location      conditions temperature humidity %cloudy  wind"
    )
    print(
        "-----------------  ------------- ---------- ----------- -------- ------- -------"
    )
    for city in forecasts:
        print(f"{forecasts[city]['timestamp'][:16]}   ", end="")
        print(f"{city}".ljust(16), end="")
        print(f"{forecasts[city]['conditions'].ljust(13)}", end="")
        print(f"{forecasts[city]['temperature']}F        ", end="")
        print(f"{forecasts[city]['humidity']}%     ", end="")
        print(f"{forecasts[city]['perc_cloudy']:>3}%   ", end="")
        print(f"{forecasts[city]['wind']}")


if __name__ == "__main__":
    main()
