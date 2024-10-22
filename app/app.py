from flask import Flask, jsonify, request
import requests
import json
import os
from models import db, WeatherData  # Import the db and model

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'  # SQLite database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # Initialize the SQLAlchemy object

@app.before_request
def create_tables():
    db.create_all()  # Create tables before the first request
API_KEY='edcf3000bfdd30731e494b719c606365'


@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch():
    cities = ['London', 'New York', 'Tokyo']
    city = str(request.json.get('city'))
    results = {}

    if city in cities:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
        response = requests.get(url)
        weather_data= response.json()
        if response.status_code == 200:
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
        else:
            return jsonify({'error': 'City not found'}), 404

    return jsonify({'status': 'success', 'data': results}), 200

if __name__ == '__main__':
    app.run(debug=True)