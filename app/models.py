from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    weather = db.Column(db.String(50))
    temp = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.String(50))
    wind_speed = db.Column(db.String(50))
    visibility = db.Column(db.String(50))
    date_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WeatherData {self.city} at {self.date_time}>"
