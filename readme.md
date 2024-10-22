# Weather App

## Description
This is an app that is built using flask framework for monitoring the weather of 5 cities.

## Features

- **Display Weather**: Shows weather information for 5 cities.
- **Threading**: Fetches data from the OpenWeather API at user-defined intervals.
- **Dominant Weather**: Identifies the dominant weather condition in each city.
- **Temperature Data**: Allows various temperature calculations.
- **Temperature Alerts**: Notifies users with background color changes and home screen notifications for temperature alerts.



## Project Structure
  - `static/`: Contains static files (CSS, JavaScript).
      - `style.css`: CSS styles.
  - `templates/`:
      - `index.html`: Main UI template.
      - `city.html`: Each city data
      -`settings.html`:Update the time interval
- `requirements.txt`: Lists the dependencies.
- `main.py`: The entry point of the application.
- `README.md`: This documentation file.

## Database

**Settings table** : To store time interval for refresh
**Weather table** : To store weather data
**Temperature table**: To store threshold temperature value  

 ### Prerequisites
  - Python 3.6 or higher
  - Flask
  - SQLite (for database)

### Build and Install
  ###  Create a virtual environment 
    python -m venv venv
  ### Initialize the virtual environment 
    venv/Scripts/activate
  ### Install dependencies:
      pip install -r requirements.txt
  ### Run the application:
      python app.py
  Open your web browser and go to `http://127.0.0.1:5000/`.