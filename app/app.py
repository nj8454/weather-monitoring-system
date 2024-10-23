from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import requests
import json
import time
from datetime import datetime, timedelta
from sqlalchemy import desc
from models import db, WeatherData

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Constants
API_KEY = 'edcf3000bfdd30731e494b719c606365'
DEFAULT_CITIES = ['Mumbai', 'Bengaluru', 'Delhi', 'Kolkata', 'Chennai', 'Hyderabad']

def init_db():
    with app.app_context():
        db.create_all()

def fetch_and_store_default_city_weather(city):
    """Fetch and store weather data for default cities with specified fields"""
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
        response = requests.get(url)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # Create new weather record with all specified fields
            weather_record = WeatherData(
                city=city,
                weather=weather_data['weather'][0]['description'],
                temp=weather_data['main']['temp'],
                feels_like=weather_data['main']['feels_like'],
                humidity=str(weather_data['main']['humidity']),
                wind_speed=str(weather_data['wind']['speed']),
                visibility=str(weather_data['visibility']/1000),
                date_time=datetime.utcnow()
            )
            
            # Store in database
            with app.app_context():
                db.session.add(weather_record)
                db.session.commit()
            
            print(f"Weather data stored for {city} at {datetime.now()}")
            return True
        else:
            print(f"Failed to fetch weather data for {city}")
            return False
            
    except Exception as e:
        print(f"Error fetching weather data for {city}: {str(e)}")
        return False

def fetch_default_cities():
    """Fetch weather data for all default cities"""
    print(f"Fetching weather data for default cities at {datetime.now()}")
    for city in DEFAULT_CITIES:
        fetch_and_store_default_city_weather(city)

def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        with app.app_context():
            fetch_default_cities()
        time.sleep(300)  # Sleep for 5 minutes (300 seconds)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current-weather', methods=['POST'])
def fetch_current_weather_data():
    """API endpoint to fetch current weather data for a city"""
    try:
        data = request.get_json()
        city = data.get('city')
        
        if not city:
            return jsonify({'status': 'error', 'error': 'City parameter is required'}), 400

        # Get the latest record from database for default cities
        if city in DEFAULT_CITIES:
            latest_record = WeatherData.query.filter_by(city=city).order_by(desc(WeatherData.date_time)).first()
            
            if latest_record:
                return jsonify({
                    'status': 'success',
                    'data': {
                        'city': latest_record.city,
                        'weather': latest_record.weather,
                        'temp': latest_record.temp,
                        'feels_like': latest_record.feels_like,
                        'humidity': latest_record.humidity,
                        'wind_speed': latest_record.wind_speed,
                        'visibility': latest_record.visibility,
                        'date_time': latest_record.date_time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                })
        
        # For all cities (including non-default ones), fetch current weather from API
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
        response = requests.get(url)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # For default cities, store the data
            if city in DEFAULT_CITIES:
                weather_record = WeatherData(
                    city=city,
                    weather=weather_data['weather'][0]['description'],
                    temp=weather_data['main']['temp'],
                    feels_like=weather_data['main']['feels_like'],
                    humidity=str(weather_data['main']['humidity']),
                    wind_speed=str(weather_data['wind']['speed']),
                    visibility=str(weather_data['visibility']/1000),
                    date_time=datetime.utcnow()
                )
                db.session.add(weather_record)
                db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'city': city,
                    'weather': weather_data['weather'][0]['description'],
                    'temp': weather_data['main']['temp'],
                    'feels_like': weather_data['main']['feels_like'],
                    'humidity': weather_data['main']['humidity'],
                    'wind_speed': weather_data['wind']['speed'],
                    'visibility': weather_data['visibility']/1000,
                    'date_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        else:
            return jsonify({'status': 'error', 'error': 'City not found'}), 404
                
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/weather-history', methods=['POST'])
def fetch_weather_history_data():
    """API endpoint to fetch weather history data for a city"""
    try:
        data = request.get_json()
        city = data.get('city')
        
        if not city:
            return jsonify({'status': 'error', 'error': 'City parameter is required'}), 400

        # Get all records from database for default cities
        if city in DEFAULT_CITIES:
            records = WeatherData.query.filter_by(city=city).order_by(desc(WeatherData.date_time)).all()
            
            if records:
                data = []
                for record in records:
                    data.append({
                        'city': record.city,
                        'weather': record.weather,
                        'temp': record.temp,
                        'feels_like': record.feels_like,
                        'humidity': record.humidity,
                        'wind_speed': record.wind_speed,
                        'visibility': record.visibility,
                        'date_time': record.date_time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                return jsonify({'status': 'success', 'data': data})
            else:
                return jsonify({'status': 'error', 'error': 'No data found'}), 404
        else:
            # For non-default cities, return error
            return jsonify({'status': 'error', 'error': 'City not supported'}), 404
                
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


if __name__ == '__main__':
    init_db()
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    app.run(debug=True)