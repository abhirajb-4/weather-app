import requests
from flask import Flask, render_template, request
from datetime import datetime
import sqlite3
import threading
import time

app = Flask(__name__)

# Global variable to store the latest weather data
latest_weather_data = []

# Setup SQLite Database
def init_db():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            main_weather TEXT,
            temperature REAL,
            feels_like REAL,
            humidity INTEGER,
            wind_speed REAL,
            date DATETIME,
            time DATETIME
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            interval INTEGER
        )
    """)
    
    cursor.execute("INSERT OR IGNORE INTO settings (id, interval) VALUES (1, 600)")  # Default 10 minutes
    conn.commit()
    conn.close()

# Function to fetch weather data for all cities
def fetch_weather_data_for_cities():
    API_KEY = 'a965ff7387fac10a0d5f1088ef913ff5'
    cities = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']
    weather_data = []

    for city in cities:
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            weather_info = response.json()
            city_weather = {
                'city': weather_info['name'],
                'main_weather': weather_info['weather'][0]['main'],
                'temperature': round(weather_info['main']['temp'] - 273.15, 2),
                'feels_like': round(weather_info['main']['feels_like'] - 273.15, 2),
                'humidity': weather_info['main']['humidity'],
                'wind_speed': weather_info['wind']['speed'],
                'date': datetime.fromtimestamp(weather_info['dt']).strftime('%Y-%m-%d'),
                'time': datetime.fromtimestamp(weather_info['dt']).strftime('%H:%M:%S')
            }
            weather_data.append(city_weather)

            # Insert data into database
            with sqlite3.connect('weather.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO weather (city, main_weather, temperature, feels_like, humidity, wind_speed, date, time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (city_weather['city'], city_weather['main_weather'], city_weather['temperature'],
                      city_weather['feels_like'], city_weather['humidity'], city_weather['wind_speed'],
                      city_weather['date'], city_weather['time']))
        else:
            print(f"Failed to get data for {city}: {response.status_code}")

    return weather_data

# Background thread to fetch weather data at intervals
def fetch_weather_data():
    global latest_weather_data
    while True:
        latest_weather_data = fetch_weather_data_for_cities()

        # Commit changes to the database
        with sqlite3.connect('weather.db') as conn:
            conn.commit()

        # Get user-defined interval
        with sqlite3.connect('weather.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT interval FROM settings WHERE id = 1")
            interval = cursor.fetchone()[0]  # Get the interval in seconds
        
        time.sleep(interval)

@app.route('/')
def index():
    global latest_weather_data

    # Get user-defined interval
    with sqlite3.connect('weather.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT interval FROM settings WHERE id = 1")
        current_interval = cursor.fetchone()[0]

    # Ensure latest_weather_data is populated
    if not latest_weather_data:
        latest_weather_data = fetch_weather_data_for_cities()

    return render_template('index.html', weather_data=latest_weather_data, current_interval=current_interval)

@app.route('/city')
def city_weather():
    city = request.args.get('city')

    with sqlite3.connect('weather.db') as conn:
        cursor = conn.cursor()

        # Fetch the latest weather details for the specified city
        cursor.execute("""
            SELECT * FROM weather 
            WHERE city = ? 
            ORDER BY date DESC, time DESC 
            LIMIT 1
        """, (city,))
        weather_info = cursor.fetchone()

        # Fetch temperature records for the current date
        cursor.execute("""
            SELECT temperature FROM weather 
            WHERE city = ? 
            AND date = DATE('now')
        """, (city,))
        temperature_records = cursor.fetchall()

        # Fetch dominant weather condition for the current date
        cursor.execute("""
            SELECT main_weather, COUNT(*) as count 
            FROM weather 
            WHERE city = ? 
            AND date = DATE('now') 
            GROUP BY main_weather 
            ORDER BY count DESC 
            LIMIT 1
        """, (city,))
        dominant_weather_info = cursor.fetchone()

    if weather_info:
        temp_values = [temp[0] for temp in temperature_records]
        min_temp = min(temp_values) if temp_values else None
        max_temp = max(temp_values) if temp_values else None
        avg_temp = round(sum(temp_values) / len(temp_values), 2) if temp_values else None

        weather_data = {
            'city': weather_info[1],
            'main_weather': weather_info[2],
            'temperature': weather_info[3],
            'feels_like': weather_info[4],
            'humidity': weather_info[5],
            'wind_speed': weather_info[6],
            'date': weather_info[7],
            'time': weather_info[8],
            'min_temp': min_temp,
            'max_temp': max_temp,
            'avg_temp': avg_temp,
            'dominant': dominant_weather_info[0] if dominant_weather_info else None,
        }
        return render_template('city.html', weather=weather_data)
    else:
        return f"No data found for {city}", 404
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    update_status = None

    if request.method == 'POST':
        new_interval = request.form.get('interval', type=int)
        if new_interval is not None:
            cursor.execute("UPDATE settings SET interval = ? WHERE id = 1", (new_interval,))
            conn.commit()
            update_status = 'success'
        else:
            update_status = 'no_update'

    cursor.execute("SELECT interval FROM settings WHERE id = 1")
    current_interval = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template('settings.html', current_interval=current_interval, update_status=update_status)

if __name__ == '__main__':
    init_db()  # Initialize the database
    # Start the background thread for fetching weather data
    threading.Thread(target=fetch_weather_data, daemon=True).start()
    app.run(debug=True)
