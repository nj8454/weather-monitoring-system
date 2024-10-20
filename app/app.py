from flask import Flask, jsonify
import requests
import json
import os

app = Flask(__name__)
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
    # List of cities you want to fetch weather data for
    cities = ['London', 'New York', 'Tokyo']
    results = {}
    
    for city in cities:
        weather_response = fetch_weather(city)
        results[city] = weather_response.json()
    
    # Here, you might want to save the results to a file or database
    with open('weather_data.json', 'w') as f:
        json.dump(results, f)
    
    return jsonify({'status': 'success', 'data': results}), 200

if __name__ == '__main__':
    app.run(debug=True)