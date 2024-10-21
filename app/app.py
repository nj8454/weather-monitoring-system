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
    cities = ['London', 'New York', 'Tokyo']
    results = {}

    try:
        for city in cities:
            weather_response = fetch_weather(city)
            if weather_response[1] == 200:  # Check the status code
                weather_data = weather_response[0].json
                city_name = weather_data['name']
                main_weather = weather_data['weather'][0]['main']
                temperature = weather_data['main']['temp']
                feels_like = weather_data['main']['feels_like']

                # Create a new WeatherData object
                weather_record = WeatherData(city=city_name, main=main_weather, temp=temperature, feels_like=feels_like)

                # Store the record in the database
                db.session.add(weather_record)
                db.session.commit()

                current_app.logger.info(f"Stored data for {city_name}")

                results[city] = weather_data

        return jsonify({'status': 'success', 'data': results}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"An error occurred: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-stored-data', methods=['GET'])
def get_stored_data():
    data = WeatherData.query.all()
    return jsonify([{
        'city': item.city,
        'temperature': item.temp,
        'main': item.main,
        'feels_like': item.feels_like,
        'date_time': str(item.date_time)  # Convert datetime to string
    } for item in data])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True)