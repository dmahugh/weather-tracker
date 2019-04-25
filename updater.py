"""Gets weather forecasts from OpenWeatherMap API for tracked locations and
stores them in the Cloud SQL database.

Before running this code, open a command window and run this command to launch
the Cloud SQL proxy:
cloud_sql_proxy -instances=<database_instance_connection_string>
"""
import requests

import defaults
from dbfunctions import db_connection


def get_forecast_api(owm_id):
    """Gets a forecast from the OpenWeatherMap API.

    Args:
        owm_id: a valid OpenWeatherMap location ID

    Returns:
        A tuple containing the JSON data returned for this forecast and
        the HTTP status code for the API call.
    """
    response = requests.get(
        (
            f"http://api.openweathermap.org/data/2.5"
            f"/forecast?id={owm_id}&APPID={defaults.API_KEY}"
        )
    )
    return response.json(), response.status_code


def save_forecasts(connection, forecast_data):
    """Saves a forecast retrieved from OpenWeatherMap API.

    Args:
        connection: a pymysql connection object
        forecast_data: the JSON payload returned by the OpenWeatherMap API
        for a single location. Note that this payload contains 40 discrete
        forecasts, one every 3 hours for the next 5 days.

    Returns:
        none
    """
    cursor = connection.cursor()

    location_id = forecast_data["city"]["id"]
    city = f"{forecast_data['city']['name']}, {forecast_data['city']['country']}"

    for forecast in forecast_data["list"]:
        # For each forecast, store it in the database. There should be
        # 40 forecasts total: one every 3 hours for the next 5 days.
        kelvin_temp = forecast["main"]["temp"]
        temp = int(1.8 * (kelvin_temp - 273) + 32)  # convert to Farenheit
        wind = wind_format(forecast["wind"]["speed"], forecast["wind"]["deg"])
        icon_url = (
            f'http://openweathermap.org/img/w/{forecast["weather"][0]["icon"]}.png'
        )
        columns = (
            "Epoch, ForecastDT, City, LocationID, Conditions,"
            " Temp, Humidity, Cloudy, Wind, IconURL"
        )
        values = (
            f'{forecast["dt"]}, "{forecast["dt_txt"]}", "{city}",'
            f' "{location_id}", "{forecast["weather"][0]["main"]}",'
            f' {temp}, {int(forecast["main"]["humidity"])},'
            f' {int(forecast["clouds"]["all"])}, "{wind}", "{icon_url}"'
        )
        cursor.execute(f"INSERT INTO Forecast ({columns}) values ({values})")

    connection.commit()


def main():
    """Retrieves the latest forecasts from OpenWeatherMap for all tracked
    locations and stores them in the wtracker database.

    Args:
        none (looks to the Location.Tracked column to determine which locations
        are being tracked)

    Returns:
        none
    """
    connection = db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT LocationID, City, Country FROM Location WHERE Tracked=TRUE")
    rows = cursor.fetchall()
    for owm_id, city, country in rows:
        print(f"Updating location {owm_id}: {city}, {country} ... ", end="")
        forecast_data, status_code = get_forecast_api(owm_id)
        if str(status_code).startswith("2"):
            save_forecasts(connection, forecast_data)
        else:
            print(f"REQUEST FAILED: status code {status_code}")
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM Forecast WHERE LocationID={owm_id}")
        total_rows = cursor.fetchall()[0][0]
        print(f"{total_rows} total forecasts")
    print(f"{len(rows)} locations updated")
    connection.close()


def wind_format(speed, direction):
    """Converts a wind speed and direction into a string formatted for user
    display.

    Args:
        speed: wind speed
        direction: window direction (in degrees: 0 is north, 90 is east, etc.)

    Returns:
        A string containing the speed and direction, such as "25 NW".
    """
    wind = str(int(speed)) + " "
    if 22.5 < direction <= 67.5:
        wind += "NE"
    if 67.5 < direction <= 112.5:
        wind += "E"
    if 112.5 < direction <= 157.5:
        wind += "SE"
    if 157.5 < direction <= 202.5:
        wind += "S"
    if 202.5 < direction <= 247.5:
        wind += "SW"
    if 247.5 < direction <= 292.5:
        wind += "W"
    if 292.5 < direction <= 337.5:
        wind += "NW"
    else:
        wind += "N"
    return wind


if __name__ == "__main__":
    main()
