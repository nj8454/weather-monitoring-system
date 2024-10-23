from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import requests
import json
import schedule
import time
import os
from sqlalchemy import desc, func  # Import desc from SQLAlchemy
from models import db, WeatherData  # Import the db and model

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'  # SQLite database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # Initialize the SQLAlchemy object

@app.before_request
def create_tables():
    db.create_all()  # Create tables before the first request
API_KEY='edcf3000bfdd30731e494b719c606365'

default_cities = ['Mumbai', 'Bengaluru', 'Delhi', 'Kolkata', 'Chennai', 'Hyderabad']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch():
    data = request.get_json()
    city = data.get('city')
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    weather_data = response.json()
    
    if response.status_code == 200:
        city_name = weather_data['name']
        weather = weather_data['weather'][0]['main']
        temperature = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        visibility = weather_data['visibility']/1000

        # Create a new WeatherData object
        weather_record = WeatherData(city=city_name, weather=weather, temp=temperature, feels_like=feels_like, humidity=humidity, wind_speed=wind_speed, visibility=visibility)

        # Store the record in the database
        db.session.add(weather_record)
        db.session.commit()
        return jsonify({'status': 'success', 'data': {city: weather_data}})
    else:
        return jsonify({'status': 'error', 'error': 'City not found'}), 404


@app.route('/get-latest-weather/<city>', methods=['GET'])
def get_latest_weather(city):
    latest_record = WeatherData.query.filter_by(city=city).order_by(desc(WeatherData.date_time)).first()
    if latest_record:
        last_three_records = WeatherData.query.filter_by(city=city).order_by(desc(WeatherData.date_time)).limit(3).all()
        high_temp = all(record.temp > 35 for record in last_three_records)
        return jsonify({
            'status': 'success',
            'data': {
                'temp': latest_record.temp,
                'weather': latest_record.weather,
                'humidity': latest_record.humidity,
                'wind_speed': latest_record.wind_speed,
                'visibility': latest_record.visibility
            },
            'high_temp': high_temp
        })
    else:
        return jsonify({'status': 'error', 'error': 'No data found for this city'}), 404


def trigger_fetch_for_cities():
    for city in default_cities:
        response = app.test_client().post('/trigger-fetch', json={'city': city})
        if response.status_code != 200:
            print(f'Error fetching data for {city}')

# Schedule the job every 5 minutes
schedule.every(5).minutes.do(trigger_fetch_for_cities)

# Run the job immediately at startup
trigger_fetch_for_cities()

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/get-historical-data/<city>', methods=['GET'])
def get_historical_data(city):
    # Get daily averages for the past 7 days
    daily_data = db.session.query(
        func.date(WeatherData.date_time).label('date'),
        func.avg(WeatherData.temp).label('avg_temp'),
        func.max(WeatherData.temp).label('max_temp'),
        func.min(WeatherData.temp).label('min_temp'),
        func.avg(WeatherData.humidity).label('avg_humidity')
    ).filter(
        WeatherData.city == city
    ).group_by(
        func.date(WeatherData.date_time)
    ).order_by(
        func.date(WeatherData.date_time).desc()
    ).limit(7).all()

    # Get alert history
    alerts = db.session.query(WeatherData).filter(
        WeatherData.city == city,
        WeatherData.temp > 35
    ).order_by(WeatherData.date_time.desc()).limit(10).all()

    return jsonify({
        'daily_data': [{
            'date': str(record.date),
            'avg_temp': float(record.avg_temp),
            'max_temp': float(record.max_temp),
            'min_temp': float(record.min_temp),
            'avg_humidity': float(record.avg_humidity)
        } for record in daily_data],
        'alerts': [{
            'date_time': str(alert.date_time),
            'temp': alert.temp
        } for alert in alerts]
    })


if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    app.run(debug=True)