from datetime import datetime
import gzip
import pickle
import json
import os
from PIL import Image
import requests
import PySimpleGUI as sg

sg.ChangeLookAndFeel('light blue')
GOLD = "#FFC13F"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        with open(relative_path) as f:
            return relative_path
    except Exception:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)


# Get saved list of us cities
with open(resource_path('app data/cities.pkl'), 'rb') as file:
    CITIES = pickle.load(file)

# Get api key
with open(resource_path('app data/api-key.txt')) as f:
    API_KEY = f.read()

# Default parameters and endpoint
with open(resource_path('app data/default_city_key.pkl'), 'rb') as file:
    CITY_KEY = pickle.load(file)

CITY_DATA = CITIES[CITY_KEY]
CITY = CITY_DATA[2]
CITY_STR = f"{CITY_DATA[2]},{CITY_DATA[0]}"
UNITS = "imperial"  # default: kelvin, metric: celsius, imperial: fahrenheit


def update_list_of_cities():
    """ Update the list of cities from the openweathermap api list """
    url = "http://bulk.openweathermap.org/sample/city.list.json.gz"
    with gzip.open(requests.get(url, stream=True).raw, 'rb') as file:
        data = json.load(file)

    city_list = [[row.get('country'), row.get('state'), row.get('name')] for row in data]   
    city_dict = {"--".join(row): row for row in city_list if row[0] != ''}

    with open(resource_path('app data/cities.pkl'), 'wb') as file:
        pickle.dump(city_dict, file)


def request_weather_data(city_str, units, api_key):
    """ Request weather data from endpoint"""
    endpoint = f"http://api.openweathermap.org/data/2.5/weather?q={city_str}&APPID={api_key}&units={units}"
    request = requests.get(endpoint)
    if request.ok:
        weather = request.json()

    app_data = {}

    # Get all relevant variables from request variable
    app_data['City'] = weather.get('name').title()
    app_data['Description'] = weather.get('weather')[0].get('description')
    app_data['Temp'] = "{:,.0f}°F".format(weather.get('main').get('temp'))
    app_data['Feels Like'] = "{:,.0f}°F".format(weather.get('main').get('feels_like'))
    app_data['Wind'] = "{:,.1f} m/h".format(weather.get('wind').get('speed'))
    app_data['Humidity'] = "{:,d}%".format(weather.get('main').get('humidity'))
    app_data['Precip 1hr'] = None if not weather.get('rain') else "{} mm".format(weather.get('rain').get('1h'))
    app_data['Pressure'] = "{:,d} hPa".format(weather.get('main').get('pressure'))

    # Get the weather icon and save locally
    weather_icon = "http://openweathermap.org/img/wn/{}@2x.png".format(weather['weather'][0]['icon'])
    req = requests.get(weather_icon, stream=True)
    img = Image.open(req.raw)
    img.save(resource_path('app data/current_weather.png'))
    app_data['Icon'] = resource_path('app data/current_weather.png')

    # Get update time and date
    app_data['Updated'] = datetime.now().strftime("%B %d %I:%M %p")

    return app_data


def layout_metric(metric):
    """ Return a pair of labels for each metric """
    label = sg.Text(metric, font=('Arial', 10), pad=(0, 0), size=(9, 1))
    measure = sg.Text(metric, font=('Arial', 10, 'bold'), pad=(0, 0), size=(9, 1), key=metric)
    return [label, measure]


def app_window(app_data):
    """ Build application window """
    app_data = request_weather_data(CITY_STR, UNITS, API_KEY)

    col1 = sg.Column([[sg.Text(app_data['City'], font=('Arial Rounded MT Bold', 14), pad=((15, 0), (25, 0)), background_color=GOLD, enable_events=True, size=(200, 1), key='City')],
                     [sg.Text(app_data['Description'], font=('Arial', 12), pad=((15, 0), (0, 0)), background_color=GOLD, key='Description')]],
        pad=(0, 0), size=(200, 100), background_color=GOLD, key='COL1')
    
    col2 = sg.Column([[sg.Image(filename=app_data['Icon'], pad=(0, 0), background_color=GOLD, size=(150, 100), key='Icon')]],
        pad=(0, 0), size=(150, 100), background_color=GOLD, element_justification='center', key='COL2')
    
    col3 = sg.Column([[sg.Text(text=app_data['Temp'], font=('Haettenschweiler', 70), pad=(15, 0), key='Temp')]],
        pad=((15, 15), (0, 0)), size=(150, 125))
    
    col4 = sg.Column([layout_metric('Feels Like'), layout_metric('Wind'), layout_metric('Humidity'),
                      layout_metric('Precip 1hr'), layout_metric('Pressure')],
        pad=(0, 0), size=(200, 125))
    
    col5 = sg.Column([[sg.Text(app_data['Updated'], background_color=GOLD, key='Updated')]],
        pad=(0, 0), size=(100, 30), background_color=GOLD, key='TIME')

    layout = [[col1, col2], [col3, col4], [col5]]

    window = sg.Window(layout=layout, title='WeatherApp', size=(350, 255), margins=(0, 0), element_justification='center',
        finalize=True, return_keyboard_events=True, no_titlebar=True, grab_anywhere=True, keep_on_top=True)

    for key in ['COL1', 'COL2', 'TIME']:
        window[key].expand(expand_x=True)

    return window


def update_weather(city_str, units, api_key, window):
    """ Update weather information on existing window """
    app_data = request_weather_data(city_str, units, api_key)
    metrics = ['City', 'Temp', 'Feels Like', 'Wind', 'Humidity', 'Precip 1hr',
               'Description', 'Icon', 'Pressure', 'Updated']
    for metric in metrics:
        window[metric].update(app_data.get(metric))


def city_select_popup():
    """ PopUP to request city from user or return default """
    global CITY_KEY, CITY_DATA, CITY, CITY_STR
    # us cities only
    cities = sorted([x for x in CITIES.keys() if x.startswith("US")])
    layout = [[sg.Combo(values=cities, default_value=CITY_KEY, size=(25, 15), font=('Arial', 14), key='SELECTION', enable_events=True)]]

    window = sg.Window(layout=layout, title='Select City', keep_on_top=True, no_titlebar=True, background_color=GOLD)

    _, combo_value = window.read()
    CITY_KEY = combo_value['SELECTION']
    CITY_DATA = CITIES[CITY_KEY]
    CITY = CITY_DATA[2]
    CITY_STR = f"{CITY_DATA[2]},{CITY_DATA[0]}"
    
    with open(resource_path('app data/default_city_key.pkl'), 'wb') as file:
        pickle.dump(CITY_KEY, file)

    window.close()


def main(refresh_rate):
    """ The main programm routine """
    app_data = request_weather_data(CITY_STR, UNITS, API_KEY)
    window = app_window(app_data)
    timeout_minutes = refresh_rate * (60 * 1000) # refresh rate is in minutes

    while True:
        event, _ = window.read(timeout=timeout_minutes)
        if event in(None, 'Escape:27'):
            break
        if event == 'City':
            city_select_popup()

        update_weather(CITY_STR, UNITS, API_KEY, window)


if __name__ == '__main__':
    print("Starting program...")
    main(refresh_rate=10)