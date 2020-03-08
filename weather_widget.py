import datetime
import base64
from urllib import request
import json
import PySimpleGUI as sg


"""
    THEMES
    You can change the theme by removing the hard-coded background color and
    uncommenting the `theme_text_color` function, which will return the appropriate
    colors when using standard PSG themes."""

sg.ChangeLookAndFeel('lightblue')
BG_COLOR = "#FFC13F" #sg.theme_text_color()
TXT_COLOR = "#000000" #sg.theme_background_color()
ALPHA = 0.8

APP_DATA = {
    'City': 'Charlotte',
    'Country': 'US',
    'Postal': None,
    'Description': 'clear skys',
    'Temp': 101.0,
    'Feels Like': 72.0,
    'Wind': 0.0,
    'Humidity': 0,
    'Precip 1hr': 0.0,
    'Pressure': 0,
    'Updated': 'Not yet updated',
    'Icon': None,
    'Units': 'Imperial'
}

API_KEY = "786af9fe6332d5da4af55ec5a90c4d4e"

def create_endpoint(endpoint_type=0):
    """ Create the api request endpoint
    {0: default, 1: zipcode, 2: city_name}"""
    if endpoint_type == 1:
        try:
            endpoint = f"http://api.openweathermap.org/data/2.5/weather?zip={APP_DATA['Postal']},us&appid={API_KEY}&units={APP_DATA['Units']}"
            return endpoint
        except ConnectionError:
            return
    elif endpoint_type == 2:
        try:
            endpoint = f"http://api.openweathermap.org/data/2.5/weather?q={APP_DATA['City'].replace(' ','%20')},us&APPID={API_KEY}&units={APP_DATA['Units']}"
            return endpoint
        except ConnectionError:
            return
    else:
        return


def request_weather_data(endpoint):
    """ Send request for updated weather data """
    global APP_DATA
    if endpoint is None:
        return
        sg.popup_error('Could not connect to api.', keep_on_top=True)
    else:
        try:
            response = request.urlopen(endpoint)
        except request.HTTPError:
            sg.popup_error('Information could not be found.', keep_on_top=True)
            return
    
    if response.reason == 'OK':
        weather = json.loads(response.read())
        APP_DATA['City'] = weather['name'].title()
        APP_DATA['Description'] = weather['weather'][0]['description']
        APP_DATA['Temp'] = "{:,.0f}°F".format(weather['main']['temp'])
        APP_DATA['Humidity'] = "{:,d}%".format(weather['main']['humidity'])
        APP_DATA['Pressure'] = "{:,d} hPa".format(weather['main']['pressure'])
        APP_DATA['Feels Like'] = "{:,.0f}°F".format(weather['main']['feels_like'])
        APP_DATA['Wind'] = "{:,.1f} m/h".format(weather['wind']['speed'])
        APP_DATA['Precip 1hr'] = None if not weather.get('rain') else "{:,d} mm".format(weather['rain']['1hr'])
        APP_DATA['Updated'] = 'Updated: ' + datetime.datetime.now().strftime("%B %d %I:%M:%S %p")
        
        icon_url = "http://openweathermap.org/img/wn/{}@2x.png".format(weather['weather'][0]['icon'])
        APP_DATA['Icon'] = base64.b64encode(request.urlopen(icon_url).read())


def metric_row(metric):
    """ Return a pair of labels for each metric """
    lbl = sg.Text(metric, font=('Arial', 10), pad=(15, 0), size=(9, 1))
    num = sg.Text(APP_DATA[metric], font=('Arial', 10, 'bold'), pad=(0, 0), size=(9, 1), key=metric)
    return [lbl, num]


def create_window():
    """ Create the application window """
    col1 = sg.Column(
        [[sg.Text(APP_DATA['City'], font=('Arial Rounded MT Bold', 18), pad=((10, 0), (50, 0)), size=(18, 1), background_color=BG_COLOR, text_color=TXT_COLOR, key='City')],
        [sg.Text(APP_DATA['Description'], font=('Arial', 12), pad=(10, 0), background_color=BG_COLOR, text_color=TXT_COLOR, key='Description')]],
            background_color=BG_COLOR, key='COL1')

    col2 = sg.Column(
        [[sg.Text('×', font=('Arial Black', 16), pad=(0, 0), justification='right', background_color=BG_COLOR, text_color=TXT_COLOR, enable_events=True, key='-QUIT-')],
        [sg.Image(data=APP_DATA['Icon'], pad=((5, 10), (0, 0)), size=(100, 100), background_color=BG_COLOR, key='Icon')]],
            element_justification='center', background_color=BG_COLOR, key='COL2')

    col3 = sg.Column(
        [[sg.Text(APP_DATA['Updated'], font=('Arial', 8), background_color=BG_COLOR, text_color=TXT_COLOR, key='Updated')]],
            pad=(10, 5), element_justification='left', background_color=BG_COLOR, key='COL3')

    col4 = sg.Column(
        [[sg.Text('click to change city', font=('Arial', 8, 'italic'), background_color=BG_COLOR, text_color=TXT_COLOR, enable_events=True, key='-CHANGE-')]],
            pad=(10, 5), element_justification='right', background_color=BG_COLOR, key='COL4')

    top_col = sg.Column([[col1, col2]], pad=(0, 0), background_color=BG_COLOR, key='TopCOL')

    bot_col = sg.Column([[col3, col4]], pad=(0, 0), background_color=BG_COLOR, key='BotCOL')

    lf_col = sg.Column(
        [[sg.Text(APP_DATA['Temp'], font=('Haettenschweiler', 90), pad=((10, 0), (0, 0)), justification='center', key='Temp')]],
            pad=(10, 0), element_justification='center', key='LfCOL')

    rt_col = sg.Column(
        [metric_row('Feels Like'), metric_row('Wind'), metric_row('Humidity'), metric_row('Precip 1hr'), metric_row('Pressure')],
            pad=((15, 0), (25, 5)), key='RtCOL')

    layout = [[top_col], [lf_col, rt_col], [bot_col]]

    window = sg.Window(layout=layout, title='Weather Widget', size=(400, 315), margins=(0, 0), finalize=True, 
        element_justification='center', keep_on_top=True, no_titlebar=True, grab_anywhere=True, alpha_channel=ALPHA)

    for col in ['COL1', 'COL2', 'TopCOL', 'BotCOL', '-QUIT-']:
        window[col].expand(expand_y=True, expand_x=True)

    for col in ['COL3', 'COL4', 'LfCOL', 'RtCOL']:
        window[col].expand(expand_x=True)

    return window


def change_city(window):
    """ Change postal zip code or city for weather api """
    global APP_DATA
    xpos, ypos = window.current_location()
    new_city = sg.popup_get_text(message="Enter 5-digit ZIP Code OR City Name", default_text=str(APP_DATA['Postal']), no_titlebar=True, keep_on_top=True, location=(xpos+405, ypos))
    if new_city is not None:
        if new_city.isnumeric() and len(new_city) == 5 and new_city is not None:
            APP_DATA['Postal'] = new_city
            request_weather_data(create_endpoint(1))
            update_metrics(window)
        else:
            APP_DATA['City'] = new_city
            request_weather_data(create_endpoint(2))
            update_metrics(window)


def update_metrics(window):
    """ Adjust the GUI to reflect the current weather metrics """
    metrics = ['City', 'Temp', 'Feels Like', 'Wind', 'Humidity', 'Precip 1hr',
               'Description', 'Icon', 'Pressure', 'Updated']
    for metric in metrics:
        if metric == 'Icon':
            window[metric].update(data=APP_DATA[metric])
        else:
            window[metric].update(APP_DATA[metric])


def main(refresh_rate):
    """ The main program routine """
    timeout_minutes = refresh_rate * (60 * 1000)

    # Try to get the current users ip location
    try:
        postal = json.loads(request.urlopen('http://ipapi.co/json').read())['postal']
        APP_DATA['Postal'] = postal
        request_weather_data(create_endpoint(1))
    except ConnectionError:
        pass

    # Create main window
    window = create_window()

    # Event loop
    while True:
        event, _ = window.read(timeout=timeout_minutes)
        if event in (None, '-QUIT-'):
            break
        if event == '-CHANGE-':
            change_city(window)

        # Update per refresh rate
        request_weather_data(create_endpoint(2))
        update_metrics(window)

    window.close()


if __name__ == '__main__':
    print("Starting program...")
    main(refresh_rate=5)