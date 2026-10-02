"""
Weather Plugin for J.A.R.V.I.S.
Fetches weather data using wttr.in (no API key required).
"""
import urllib.request
import urllib.parse
import json
import sys
sys.path.insert(0, '..')
from plugin_system import PluginBase


class WeatherPlugin(PluginBase):
    name = "weather"
    description = "Get current weather and forecasts for any location"
    version = "1.0.0"
    commands = [
        'weather', 'temperature', "what's the weather", 'how hot', 'how cold',
        'is it raining', 'will it rain', 'forecast', "today's weather"
    ]
    
    def execute(self, message, params=None):
        import re
        
        # Try to extract location from the message
        location = self._extract_location(message)
        
        try:
            weather = self._fetch_weather(location)
            if weather:
                return {
                    'success': True,
                    'response': weather,
                    'data': {'location': location}
                }
            return {
                'success': False,
                'response': f"Sir, I couldn't retrieve weather data for {location}."
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Weather service unavailable: {str(e)}"
            }
    
    def _extract_location(self, message):
        """Extract location from natural language."""
        import re
        
        # Try patterns like "weather in London", "temperature at Paris"
        patterns = [
            r'(?:weather|temperature|forecast)\s+(?:in|at|for|of)\s+(.+?)(?:\s*\?|$)',
            r'(?:how\s+(?:hot|cold|warm))\s+(?:is\s+it\s+)?(?:in|at)\s+(.+?)(?:\s*\?|$)',
            r'(?:is\s+it\s+raining)\s+(?:in|at)\s+(.+?)(?:\s*\?|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).strip()
        
        # Default location from context
        config_dir = self.context.get('config_dir', '')
        return 'Jaipur'  # Default for Divyanshu
    
    def _fetch_weather(self, location):
        """Fetch weather from wttr.in."""
        encoded = urllib.parse.quote(location)
        url = f"https://wttr.in/{encoded}?format=j1"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'JarvisAI/5.0',
            'Accept': 'application/json',
        })
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        current = data.get('current_condition', [{}])[0]
        area = data.get('nearest_area', [{}])[0]
        
        city = area.get('areaName', [{}])[0].get('value', location)
        country = area.get('country', [{}])[0].get('value', '')
        temp_c = current.get('temp_C', '?')
        temp_f = current.get('temp_F', '?')
        feels_like = current.get('FeelsLikeC', '?')
        desc = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
        humidity = current.get('humidity', '?')
        wind_speed = current.get('windspeedKmph', '?')
        wind_dir = current.get('winddir16Point', '')
        uv_index = current.get('uvIndex', '?')
        
        # Get today's forecast for high/low
        forecast = data.get('weather', [{}])[0]
        max_temp = forecast.get('maxtempC', '?')
        min_temp = forecast.get('mintempC', '?')
        
        response = (
            f"**Weather Report: {city}, {country}**\n\n"
            f"🌡️ **{temp_c}°C** ({temp_f}°F) — *{desc}*\n"
            f"🤲 Feels like: {feels_like}°C\n"
            f"📊 High/Low: {max_temp}°C / {min_temp}°C\n"
            f"💧 Humidity: {humidity}%\n"
            f"💨 Wind: {wind_speed} km/h {wind_dir}\n"
            f"☀️ UV Index: {uv_index}"
        )
        
        return response
