#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import time
import requests
import psutil
import logging
from datetime import datetime
from math import cos, sin, radians
import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

# Configurazione logging
logging.basicConfig(level=logging.DEBUG)

# Configurazione OpenWeatherMap
OPENWEATHER_API_KEY = "mettiquilatuaAPI_KEY"
CITY = "Venice,IT"

def get_wind_name(degrees):
    """Restituisce il nome del vento in base ai gradi"""
    if degrees > 337.5 or degrees <= 22.5:
        return "Tramontana"
    elif degrees <= 67.5:
        return "Grecale"
    elif degrees <= 112.5:
        return "Levante"
    elif degrees <= 157.5:
        return "Scirocco"
    elif degrees <= 202.5:
        return "Ostro"
    elif degrees <= 247.5:
        return "Libeccio"
    elif degrees <= 292.5:
        return "Ponente"
    elif degrees <= 337.5:
        return "Maestrale"


def draw_sun_icon(draw, x, y, size):
    """Disegna un'icona del sole"""
    # Cerchio centrale
    radius = size // 3
    draw.ellipse([x-radius, y-radius, x+radius, y+radius], outline=0, width=2)

    # Raggi
    ray_length = size // 2
    for i in range(8):
        angle = i * 45
        rad_angle = radians(angle)
        start_x = x + cos(rad_angle) * (radius + 5)
        start_y = y + sin(rad_angle) * (radius + 5)
        end_x = x + cos(rad_angle) * ray_length
        end_y = y + sin(rad_angle) * ray_length
        draw.line([(start_x, start_y), (end_x, end_y)], fill=0, width=2)

def draw_cloud_icon(draw, x, y, size):
    """Disegna un'icona della nuvola"""
    cloud_height = size // 2
    cloud_width = size * 3 // 4

    # Base della nuvola
    draw.ellipse([x, y, x+cloud_width, y+cloud_height], outline=0, width=2)
    draw.ellipse([x+cloud_width//2, y-cloud_height//3, x+cloud_width, y+cloud_height//2], outline=0, width=2)
    draw.ellipse([x+cloud_width//4, y-cloud_height//4, x+cloud_width*3//4, y+cloud_height//2], outline=0, width=2)

def draw_rain_icon(draw, x, y, size):
    """Disegna un'icona della pioggia"""
    # Prima disegna una nuvola più piccola
    draw_cloud_icon(draw, x, y, size * 2 // 3)

    # Aggiungi gocce di pioggia
    drop_start_y = y + size // 2
    for i in range(3):
        drop_x = x + (i * size // 3)
        draw.line([(drop_x, drop_start_y), (drop_x - size//6, drop_start_y + size//3)], fill=0, width=2)

def draw_snow_icon(draw, x, y, size):
    """Disegna un'icona della neve"""
    # Prima disegna una nuvola più piccola
    draw_cloud_icon(draw, x, y, size * 2 // 3)

    # Aggiungi fiocchi di neve
    flake_start_y = y + size // 2
    for i in range(3):
        flake_x = x + (i * size // 3)
        flake_y = flake_start_y + size // 3
        flake_size = size // 8
        draw.ellipse([flake_x-flake_size, flake_y-flake_size,
                     flake_x+flake_size, flake_y+flake_size], outline=0, width=1)

def draw_thunder_icon(draw, x, y, size):
    """Disegna un'icona del temporale"""
    # Prima disegna una nuvola
    draw_cloud_icon(draw, x, y, size * 2 // 3)

    # Aggiungi fulmine
    lightning_points = [
        (x + size//2, y + size//2),  # Inizio
        (x + size//3, y + size*2//3),  # Primo zigzag
        (x + size//2, y + size*2//3),  # Punto medio
        (x + size//3, y + size)   # Fine
    ]
    draw.line(lightning_points, fill=0, width=2)

def draw_fog_icon(draw, x, y, size):
    """Disegna un'icona della nebbia"""
    # Linee ondulate per rappresentare la nebbia
    for i in range(4):
        y_pos = y + (i * size // 4)
        points = [
            (x, y_pos),
            (x + size//4, y_pos - size//8),
            (x + size//2, y_pos),
            (x + size*3//4, y_pos - size//8),
            (x + size, y_pos)
        ]
        draw.line(points, fill=0, width=2)

def draw_weather_icon(draw, x, y, size, weather_type):
    """Funzione principale per disegnare l'icona del tempo appropriata"""
    if 'pioggia' in weather_type or 'rain' in weather_type:
        draw_rain_icon(draw, x, y, size)
    elif 'neve' in weather_type or 'snow' in weather_type:
        draw_snow_icon(draw, x, y, size)
    elif 'nuvol' in weather_type or 'cloud' in weather_type:
        draw_cloud_icon(draw, x, y, size)
    elif 'nebbia' in weather_type or 'fog' in weather_type:
        draw_fog_icon(draw, x, y, size)
    elif 'temporale' in weather_type or 'thunder' in weather_type:
        draw_thunder_icon(draw, x, y, size)
    else:  # sereno/clear come default
        draw_sun_icon(draw, x+size//2, y+size//2, size)

def draw_compass_rose(draw, x, y, radius):
    """Disegna una rosa dei venti dettagliata"""
    # Cerchi concentrici
    draw.ellipse([x-radius, y-radius, x+radius, y+radius], outline=0, width=1)
    draw.ellipse([x-radius*0.7, y-radius*0.7, x+radius*0.7, y+radius*0.7], outline=0, width=1)

    # Punti cardinali
    directions = [
        ('N', 0), ('NE', 45), ('E', 90), ('SE', 135),
        ('S', 180), ('SO', 225), ('O', 270), ('NO', 315)
    ]
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)

    for direction, angle in directions:
        # Linee principali
        rad_angle = radians(angle)
        end_x = x + cos(rad_angle) * radius
        end_y = y - sin(rad_angle) * radius
        start_x = x + cos(rad_angle) * (radius * 0.3)
        start_y = y - sin(rad_angle) * (radius * 0.3)
        draw.line([(start_x, start_y), (end_x, end_y)], fill=0, width=2 if angle % 90 == 0 else 1)

        # Testo
        text_x = x + cos(rad_angle) * (radius * 1.2) - 8
        text_y = y - sin(rad_angle) * (radius * 1.2) - 8
        draw.text((text_x, text_y), direction, font=font, fill=0)

def draw_wind_arrow(draw, x, y, radius, angle):
    """Disegna una freccia del vento stilizzata"""
    rad_angle = radians(angle)
    # Freccia principale
    end_x = x + cos(rad_angle) * radius * 0.8
    end_y = y - sin(rad_angle) * radius * 0.8
    draw.line([(x, y), (end_x, end_y)], fill=0, width=2)

    # Punta della freccia
    arrow_size = radius * 0.2
    left_angle = rad_angle + radians(150)
    right_angle = rad_angle - radians(150)
    left_x = end_x + cos(left_angle) * arrow_size
    left_y = end_y - sin(left_angle) * arrow_size
    right_x = end_x + cos(right_angle) * arrow_size
    right_y = end_y - sin(right_angle) * arrow_size
    draw.polygon([(end_x, end_y), (left_x, left_y), (right_x, right_y)], fill=0)

def get_weather():
    try:
        # Richiesta meteo corrente
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        response = requests.get(url)
        data = response.json()

        # Richiesta previsioni
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()

        return {
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'temp_min': round(data['main']['temp_min']),
            'temp_max': round(data['main']['temp_max']),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'description': data['weather'][0]['description'],
            'wind_speed': round(data['wind']['speed'] * 3.6),
            'wind_deg': data['wind'].get('deg', 0),
            'clouds': data['clouds']['all'],
            'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M'),
            'visibility': data.get('visibility', 0) / 1000,
            'forecast': forecast_data['list'][:2]  # Solo le prime 2 previsioni
        }
    except Exception as e:
        logging.error(f"Errore nel recupero dati meteo: {e}")
        return None

def get_system_stats():
    cpu_temp = None
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            cpu_temp = round(float(f.read()) / 1000, 1)
    except:
        cpu_temp = "N/A"

    return {
        'cpu_percent': psutil.cpu_percent(),
        'cpu_temp': cpu_temp,
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'uptime': round(float(open('/proc/uptime').read().split()[0]) / 3600, 1)
    }

try:
    # Inizializzazione
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()

    # Creazione immagine
    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)

    # Font
    font_digital = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 96)
    font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
    font_normal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)

    # Recupero dati
    weather = get_weather()
    stats = get_system_stats()

    if weather:
        # Divisione schermo in due parti
        draw.line([(epd.width//2, 20), (epd.width//2, epd.height-60)], fill=0, width=1)

        # Parte sinistra - Condizioni attuali
        x, y = 40, 40

        # Icona meteo grande e temperatura accanto
        draw_weather_icon(draw, x, y, 120, weather['description'].lower())
        draw.text((x + 160, y + 10), f"{weather['temp']}°", font=font_digital, fill=0)

        # Descrizione condizioni
        y += 140
        draw.text((x, y), weather['description'].capitalize(), font=font_large, fill=0)

        # Dettagli secondari
        y += 50
        details = [
            f"Percepita: {weather['feels_like']}°",
            f"Min: {weather['temp_min']}° · Max: {weather['temp_max']}°",
            f"Umidità: {weather['humidity']}%",
            f"Pressione: {weather['pressure']} hPa",
            f"Visibilità: {weather['visibility']} km",
            f"Alba: {weather['sunrise']} · Tramonto: {weather['sunset']}"
        ]

        for detail in details:
            draw.text((x, y), detail, font=font_normal, fill=0)
            y += 30

        # Parte destra - Rosa dei venti e previsioni
        x = epd.width//2 + 40
        y = 40

        # Rosa dei venti grande
        compass_x = x + 150
        compass_y = y + 100
        draw_compass_rose(draw, compass_x, compass_y, 80)
        draw_wind_arrow(draw, compass_x, compass_y, 80, weather['wind_deg'])

# Velocità e nome del vento sotto la rosa
        wind_name = get_wind_name(weather['wind_deg'])
        wind_text = f"Vento: {weather['wind_speed']} km/h - {wind_name}"
        draw.text((x + 1, y + 200), wind_text, font=font_normal, fill=0)


# Previsioni compatte
        y = 280
        draw.text((x, y), "Previsioni:", font=font_large, fill=0)
        y += 50
        x_offset = 0

        # Solo le prime 2 previsioni
        for forecast in weather['forecast'][:2]:
            temp = round(forecast['main']['temp'])
            time = datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
            prob_rain = forecast.get('pop', 0) * 100

            # Icona meteo
            draw_weather_icon(draw, x + x_offset, y, 48, forecast['weather'][0]['description'].lower())

            # Probabilità pioggia accanto all'icona
            if prob_rain > 0:
                draw.text((x + x_offset + 55, y + 15), f"{round(prob_rain)}%", font=font_small, fill=0)

            # Ora e temperatura sulla stessa riga
            draw.text((x + x_offset, y + 60), f"{time} • {temp}°", font=font_normal, fill=0)

            x_offset += 150  # Spazio tra le previsioni

    # Barra di sistema in basso
    system_y = epd.height - 40
    draw.line([(20, system_y-10), (epd.width-20, system_y-10)], fill=0, width=1)

    x = 40
    stats_list = [
        ("CPU", stats['cpu_percent']),
        ("RAM", stats['memory']),
        ("DISCO", stats['disk'])
    ]

    for label, value in stats_list:
        text = f"{label}: {value}%"
        draw.text((x, system_y), text, font=font_small, fill=0)
        x += 200

    # Data e ora
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    draw.text((epd.width-200, system_y), current_time, font=font_small, fill=0)

    # Visualizzazione
    epd.display(epd.getbuffer(image))
    epd.sleep()

except Exception as e:
    logging.error(f'Errore: {e}')
    raise e

finally:
    epd7in5_V2.epdconfig.module_exit()
