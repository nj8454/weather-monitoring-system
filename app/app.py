from flask import Flask, jsonify
import requests
import json
import os
from models import db, WeatherData  # Import the db and model

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'  # SQLite database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # Initialize the SQLAlchemy object


API_KEY='edcf3000bfdd30731e494b719c606365'

    
@app.route('/')
def index():
    return 'Wlecome to weather monitoring'

@app.route('/fetch-weather/<city>', methods=['GET'])
def fetch_weather(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return jsonify(data), 200
    else:
        return jsonify({'error': 'City not found'}), 404

@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch():
    cities = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']
    results = {}

    for city in cities:
        weather_response = fetch_weather(city)
        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            city_name = weather_data['name']
            main_weather = weather_data['weather'][0]['main']
            temperature = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']

            # Create a new WeatherData object
            weather_record = WeatherData(city=city_name, main=main_weather, temp=temperature, feels_like=feels_like)

            # Store the record in the database
            db.session.add(weather_record)
            db.session.commit()

            results[city] = weather_data

    return jsonify({'status': 'success', 'data': results}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True)