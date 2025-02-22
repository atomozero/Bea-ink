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
import xml.etree.ElementTree as ET


# Configurazione logging in italiano
class FormattatoreLogs(logging.Formatter):
    def format(self, record):
        colori = {
            logging.DEBUG: '\033[36m',     # Ciano per DEBUG
            logging.INFO: '\033[32m',      # Verde per INFO
            logging.WARNING: '\033[33m',   # Giallo per AVVISO
            logging.ERROR: '\033[31m',     # Rosso per ERRORE
            logging.CRITICAL: '\033[31m\033[1m'  # Rosso brillante per CRITICO
        }
        reset = '\033[0m'

        livelli_tradotti = {
            'DEBUG': 'DEBUG',
            'INFO': 'INFO',
            'WARNING': 'AVVISO',
            'ERROR': 'ERRORE',
            'CRITICAL': 'CRITICO'
        }

        colore = colori.get(record.levelno, '')
        livello_tradotto = livelli_tradotti.get(record.levelname, record.levelname)
        record.levelname = f'{colore}{livello_tradotto:<8}{reset}'

        if 'connectionpool' in record.name:
            if 'Starting new' in record.msg:
                return None
            if 'GET' in str(record.msg):
                parti = str(record.msg).split('"')
                if len(parti) >= 2:
                    url = parti[1].split(' ')[1]
                    stato = parti[-2]
                    return f"{record.levelname} Richiesta HTTP: {url} → Stato: {sta
to}"

        if 'e-Paper' in str(record.msg):
            msg_tradotto = str(record.msg).replace('busy', 'occupato').replace('rel
ease', 'libero')
            return f"{record.levelname} Display: {msg_tradotto}"

        msg = str(record.msg)
        msg = msg.replace('Starting new HTTP connection', 'Avvio nuova connessione
HTTP') \
                 .replace('close 5V, Module enters 0 power consumption', 'chiusura
5V, Modulo entra in risparmio energetico') \
                 .replace('spi end', 'fine comunicazione SPI')

        return f"{record.levelname} {record.name}: {msg}"

def configura_logging():
    logger_root = logging.getLogger()
    logger_root.setLevel(logging.INFO)

    for gestore in logger_root.handlers[:]:
        logger_root.removeHandler(gestore)

    gestore_console = logging.StreamHandler(sys.stdout)
    gestore_console.setFormatter(FormattatoreLogs())
    logger_root.addHandler(gestore_console)

    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

# Configurazione logging
configura_logging()

# Configurazione API
CHIAVE_OPENWEATHER = "605915fb16ba43e55a8ff6432939a79f"
CITTA = "Venice,IT"

def ottieni_ultima_notizia():
    """Recupera l'ultima notizia dal feed RSS di ANSA"""
    try:
        url = "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml"
        risposta = requests.get(url, timeout=5)
        root = ET.fromstring(risposta.content)

        # Trova il primo item nel feed
        primo_item = root.find(".//item")
        if primo_item is not None:
            titolo = primo_item.find("title").text
            data = primo_item.find("pubDate").text
            return {
                'titolo': titolo,
                'data': data
            }
    except Exception as e:
        logging.error(f"Errore nel recupero feed RSS: {e}")
        return None

def disegna_barra_notizie(disegno, y, larghezza_display, caratteri):
    """Disegna la barra delle notizie in basso"""
    notizia = ottieni_ultima_notizia()

    # Disegna prima la linea separatrice
    disegno.line([(20, y-10), (larghezza_display-20, y-10)], fill=0, width=1)

    # Disegna l'ora corrente a destra
    ora_corrente = datetime.now().strftime("%d/%m/%Y %H:%M")
    larghezza_ora = 180  # Spazio riservato per la data/ora
    disegno.text((larghezza_display-larghezza_ora-20, y), ora_corrente, font=caratt
eri['piccolo'], fill=0)

    if notizia:
        # Calcola lo spazio disponibile per il testo (considerando il margine sinis
tro e lo spazio per l'ora)
        spazio_disponibile = larghezza_display - larghezza_ora - 80  # 40px margine
 sinistro + 20px margine tra news e ora + 20px margine destro

        # Tronca il titolo se necessario
        titolo = notizia['titolo']
        pixel_per_carattere = 10  # Stima approssimativa
        lunghezza_massima = spazio_disponibile // pixel_per_carattere

        if len(titolo) > lunghezza_massima:
            titolo = titolo[:lunghezza_massima-3] + "..."

        # Disegna il titolo della notizia
        disegno.text((40, y), f"ANSA: {titolo}", font=caratteri['piccolo'], fill=0)

def disegna_icona_sole(disegno, x, y, dimensione):
    """Disegna un'icona del sole"""
    raggio = dimensione // 3
    disegno.ellipse([x-raggio, y-raggio, x+raggio, y+raggio], outline=0, width=2)
    lunghezza_raggio = dimensione // 2
    for i in range(8):
        angolo = i * 45
        angolo_rad = radians(angolo)
        inizio_x = x + cos(angolo_rad) * (raggio + 5)
        inizio_y = y + sin(angolo_rad) * (raggio + 5)
        fine_x = x + cos(angolo_rad) * lunghezza_raggio
        fine_y = y + sin(angolo_rad) * lunghezza_raggio
        disegno.line([(inizio_x, inizio_y), (fine_x, fine_y)], fill=0, width=2)

def disegna_icona_nuvola(disegno, x, y, dimensione):
    """Disegna un'icona della nuvola"""
    altezza_nuvola = dimensione // 2
    larghezza_nuvola = dimensione * 3 // 4
    disegno.ellipse([x, y, x+larghezza_nuvola, y+altezza_nuvola], outline=0, width=
2)
    disegno.ellipse([x+larghezza_nuvola//2, y-altezza_nuvola//3, x+larghezza_nuvola
, y+altezza_nuvola//2], outline=0, width=2)
    disegno.ellipse([x+larghezza_nuvola//4, y-altezza_nuvola//4, x+larghezza_nuvola
*3//4, y+altezza_nuvola//2], outline=0, width=2)

def disegna_icona_pioggia(disegno, x, y, dimensione):
    """Disegna un'icona della pioggia"""
    disegna_icona_nuvola(disegno, x, y, dimensione * 2 // 3)
    inizio_goccia_y = y + dimensione // 2
    for i in range(3):
        goccia_x = x + (i * dimensione // 3)
        disegno.line([(goccia_x, inizio_goccia_y), (goccia_x - dimensione//6, inizi
o_goccia_y + dimensione//3)], fill=0, width=2)

def disegna_icona_neve(disegno, x, y, dimensione):
    """Disegna un'icona della neve"""
    disegna_icona_nuvola(disegno, x, y, dimensione * 2 // 3)
    inizio_fiocco_y = y + dimensione // 2
    for i in range(3):
        fiocco_x = x + (i * dimensione // 3)
        fiocco_y = inizio_fiocco_y + dimensione // 3
        dim_fiocco = dimensione // 8
        disegno.ellipse([fiocco_x-dim_fiocco, fiocco_y-dim_fiocco, fiocco_x+dim_fio
cco, fiocco_y+dim_fiocco], outline=0, width=1)

def disegna_icona_temporale(disegno, x, y, dimensione):
    """Disegna un'icona del temporale"""
    disegna_icona_nuvola(disegno, x, y, dimensione * 2 // 3)
    punti_fulmine = [
        (x + dimensione//2, y + dimensione//2),
        (x + dimensione//3, y + dimensione*2//3),
        (x + dimensione//2, y + dimensione*2//3),
        (x + dimensione//3, y + dimensione)
    ]
    disegno.line(punti_fulmine, fill=0, width=2)

def disegna_icona_nebbia(disegno, x, y, dimensione):
    """Disegna un'icona della nebbia"""
    for i in range(4):
        y_pos = y + (i * dimensione // 4)
        punti = [
            (x, y_pos),
            (x + dimensione//4, y_pos - dimensione//8),
            (x + dimensione//2, y_pos),
            (x + dimensione*3//4, y_pos - dimensione//8),
            (x + dimensione, y_pos)
        ]
        disegno.line(punti, fill=0, width=2)

def disegna_icona_meteo(disegno, x, y, dimensione, tipo_meteo):
    """Funzione principale per disegnare l'icona del tempo appropriata"""
    if 'pioggia' in tipo_meteo or 'rain' in tipo_meteo:
        disegna_icona_pioggia(disegno, x, y, dimensione)
    elif 'neve' in tipo_meteo or 'snow' in tipo_meteo:
        disegna_icona_neve(disegno, x, y, dimensione)
    elif 'nuvol' in tipo_meteo or 'cloud' in tipo_meteo:
        disegna_icona_nuvola(disegno, x, y, dimensione)
    elif 'nebbia' in tipo_meteo or 'fog' in tipo_meteo:
        disegna_icona_nebbia(disegno, x, y, dimensione)
    elif 'temporale' in tipo_meteo or 'thunder' in tipo_meteo:
        disegna_icona_temporale(disegno, x, y, dimensione)
    else:
        disegna_icona_sole(disegno, x+dimensione//2, y+dimensione//2, dimensione)

def disegna_rosa_venti(disegno, x, y, raggio):
    """Disegna una rosa dei venti dettagliata"""
    disegno.ellipse([x-raggio, y-raggio, x+raggio, y+raggio], outline=0, width=1)
    disegno.ellipse([x-raggio*0.7, y-raggio*0.7, x+raggio*0.7, y+raggio*0.7], outli
ne=0, width=1)
    direzioni = [
        ('N', 0), ('NE', 45), ('E', 90), ('SE', 135),
        ('S', 180), ('SO', 225), ('O', 270), ('NO', 315)
    ]
    carattere = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bol
d.ttf', 16)
    for direzione, angolo in direzioni:
        angolo_rad = radians(angolo)
        fine_x = x + cos(angolo_rad) * raggio
        fine_y = y - sin(angolo_rad) * raggio
        inizio_x = x + cos(angolo_rad) * (raggio * 0.3)
        inizio_y = y - sin(angolo_rad) * (raggio * 0.3)
        disegno.line([(inizio_x, inizio_y), (fine_x, fine_y)], fill=0, width=2 if a
ngolo % 90 == 0 else 1)
        testo_x = x + cos(angolo_rad) * (raggio * 1.2) - 8
        testo_y = y - sin(angolo_rad) * (raggio * 1.2) - 8
        disegno.text((testo_x, testo_y), direzione, font=carattere, fill=0)

def disegna_freccia_vento(disegno, x, y, raggio, angolo):
    """Disegna una freccia del vento stilizzata"""
    angolo_rad = radians(angolo)
    fine_x = x + cos(angolo_rad) * raggio * 0.8
    fine_y = y - sin(angolo_rad) * raggio * 0.8
    disegno.line([(x, y), (fine_x, fine_y)], fill=0, width=2)
    dim_freccia = raggio * 0.2
    angolo_sinistro = angolo_rad + radians(150)
    angolo_destro = angolo_rad - radians(150)
    x_sinistro = fine_x + cos(angolo_sinistro) * dim_freccia
    y_sinistro = fine_y - sin(angolo_sinistro) * dim_freccia
    x_destro = fine_x + cos(angolo_destro) * dim_freccia
    y_destro = fine_y - sin(angolo_destro) * dim_freccia
    disegno.polygon([(fine_x, fine_y), (x_sinistro, y_sinistro), (x_destro, y_destr
o)], fill=0)

def disegna_sezione_crypto(disegno, x, y, dati_crypto, caratteri):
    """Disegna una sezione crypto pulita e minimalista"""
    larghezza_sezione = 300

    if dati_crypto:
        # Titolo della sezione (abbassato di 5px)
        y_titolo = y + 20
        disegno.text((x, y_titolo), "Crypto", font=caratteri['grande'], fill=0)

        # BTC
        y_btc = y_titolo + 60  # Spazio dopo il titolo
        disegno.text((x, y_btc), "BTC", font=caratteri['normale'], fill=0)

        # Prezzo BTC
        prezzo_btc = f"{dati_crypto['prezzo_btc']:,}€"
        x_prezzo_btc = x + larghezza_sezione - len(prezzo_btc) * 12
        disegno.text((x_prezzo_btc, y_btc), prezzo_btc, font=caratteri['normale'],
fill=0)

        # Variazione BTC
        variazione_btc = dati_crypto['variazione_btc']
        simbolo_variazione = "▲" if variazione_btc >= 0 else "▼"
        testo_variazione_btc = f"{simbolo_variazione}{abs(variazione_btc):.1f}%"
        x_variazione_btc = x + 80
        disegno.text((x_variazione_btc, y_btc), testo_variazione_btc, font=caratter
i['normale'], fill=0)

        # ETH
        y_eth = y_btc + 45  # Spazio tra BTC ed ETH
        disegno.text((x, y_eth), "ETH", font=caratteri['normale'], fill=0)

        # Prezzo ETH
        prezzo_eth = f"{dati_crypto['prezzo_eth']:,}€"
        x_prezzo_eth = x + larghezza_sezione - len(prezzo_eth) * 12
        disegno.text((x_prezzo_eth, y_eth), prezzo_eth, font=caratteri['normale'],
fill=0)

        # Variazione ETH
        variazione_eth = dati_crypto['variazione_eth']
        simbolo_variazione = "▲" if variazione_eth >= 0 else "▼"
        testo_variazione_eth = f"{simbolo_variazione}{abs(variazione_eth):.1f}%"
        x_variazione_eth = x + 80
        disegno.text((x_variazione_eth, y_eth), testo_variazione_eth, font=caratter
i['normale'], fill=0)
    else:
        disegno.text((x, y), "Dati crypto non disponibili", font=caratteri['normale
'], fill=0)

def ottieni_nome_vento(gradi):
    """Restituisce il nome tradizionale italiano del vento"""
    venti = [
        "Tramontana",    # 0° (Nord)
        "Grecale",       # 45° (Nord-Est)
        "Levante",       # 90° (Est)
        "Scirocco",      # 135° (Sud-Est)
        "Mezzogiorno",   # 180° (Sud)
        "Libeccio",      # 225° (Sud-Ovest)
        "Ponente",       # 270° (Ovest)
        "Maestrale"      # 315° (Nord-Ovest)
    ]
    indice = round(gradi / 45) % 8
    return venti[indice]

def ottieni_meteo():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITTA}&appid={CHI
AVE_OPENWEATHER}&units=metric&lang=it"
        risposta = requests.get(url)
        dati = risposta.json()

        return {
            'temperatura': round(dati['main']['temp']),
            'temperatura_percepita': round(dati['main']['feels_like']),
            'temp_min': round(dati['main']['temp_min']),
            'temp_max': round(dati['main']['temp_max']),
            'umidita': dati['main']['humidity'],
            'pressione': dati['main']['pressure'],
            'descrizione': dati['weather'][0]['description'],
            'velocita_vento': round(dati['wind']['speed'] * 3.6),
            'direzione_vento': dati['wind'].get('deg', 0),
            'nuvolosita': dati['clouds']['all'],
            'alba': datetime.fromtimestamp(dati['sys']['sunrise']).strftime('%H:%M'
),
            'tramonto': datetime.fromtimestamp(dati['sys']['sunset']).strftime('%H:
%M'),
            'visibilita': dati.get('visibility', 0) / 1000,
        }
    except Exception as e:
        logging.error(f"Errore nel recupero dati meteo: {e}")
        return None

def ottieni_prezzi_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&v
s_currencies=eur&include_24hr_change=true"
        risposta = requests.get(url)
        dati = risposta.json()
        return {
            'prezzo_btc': round(dati['bitcoin']['eur']),
            'variazione_btc': round(dati['bitcoin']['eur_24h_change'], 2),
            'prezzo_eth': round(dati['ethereum']['eur']),
            'variazione_eth': round(dati['ethereum']['eur_24h_change'], 2)
        }
    except Exception as e:
        logging.error(f"Errore nel recupero dati crypto: {e}")
        return None


try:
    # Inizializzazione
    display = epd7in5_V2.EPD()
    display.init()
    display.Clear()

    # Creazione immagine
    immagine = Image.new('1', (display.width, display.height), 255)
    disegno = ImageDraw.Draw(immagine)

    # Font
    carattere_digitale = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaV
uSansMono-Bold.ttf', 96)
    carattere_grande = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuS
ans-Bold.ttf', 36)
    carattere_normale = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVu
Sans.ttf', 24)
    carattere_piccolo = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVu
Sans.ttf', 18)

    caratteri = {
        'digitale': carattere_digitale,
        'grande': carattere_grande,
        'normale': carattere_normale,
        'piccolo': carattere_piccolo
    }

    # Recupero dati
    meteo = ottieni_meteo()
    crypto = ottieni_prezzi_crypto()
   # statistiche = ottieni_statistiche_sistema()

    if meteo:
        # Calcolo la posizione della linea centrale
        linea_centrale = (display.width//2) - 5  # Spostiamo la linea di 5px a sini
stra

        # Divisione schermo in due parti
        disegno.line([(linea_centrale, 20), (linea_centrale, display.height-60)], f
ill=0, width=1)

        # Parte sinistra - Condizioni attuali
        x, y = 30, 40
        disegna_icona_meteo(disegno, x, y, 120, meteo['descrizione'].lower())
        disegno.text((x + 160, y + 10), f"{meteo['temperatura']}°", font=carattere_
digitale, fill=0)

        y += 140
        disegno.text((x, y), meteo['descrizione'].capitalize(), font=carattere_gran
de, fill=0)

        y += 50
        dettagli = [
            f"Percepita: {meteo['temperatura_percepita']}°",
            f"Min: {meteo['temp_min']}° · Max: {meteo['temp_max']}°",
            f"Umidità: {meteo['umidita']}%",
            f"Pressione: {meteo['pressione']} hPa",
            f"Visibilità: {meteo['visibilita']} km",
            f"Alba: {meteo['alba']} · Tramonto: {meteo['tramonto']}"
        ]
        for dettaglio in dettagli:
            disegno.text((x, y), dettaglio, font=carattere_normale, fill=0)
            y += 30

        # Parte destra - Rosa dei venti e crypto
        x = linea_centrale + 40
        y = 40
        bussola_x = x + 150
        bussola_y = y + 80
        disegna_rosa_venti(disegno, bussola_x, bussola_y, 80)
        disegna_freccia_vento(disegno, bussola_x, bussola_y, 80, meteo['direzione_v
ento'])

        testo_vento = f"Vento: {meteo['velocita_vento']} km/h {ottieni_nome_vento(m
eteo['direzione_vento'])}"
        font_vento = carattere_piccolo
        bbox_testo = disegno.textbbox((0, 0), testo_vento, font=font_vento)
        larghezza_testo = bbox_testo[2] - bbox_testo[0]
        x_vento = bussola_x - (larghezza_testo // 2)
        y_vento = y + 200
        disegno.text((x_vento, y_vento), testo_vento, font=font_vento, fill=0)

        # Sezione Crypto
        disegna_sezione_crypto(disegno, x, 250, crypto, caratteri)

        # Barra notizie in basso
        y_notizie = display.height - 40
        disegna_barra_notizie(disegno, y_notizie, display.width, caratteri)

    # Visualizzazione
    display.display(display.getbuffer(immagine))
    display.sleep()

except Exception as e:
    logging.error(f'Errore: {e}')
    raise e

finally:
    epd7in5_V2.epdconfig.module_exit()
