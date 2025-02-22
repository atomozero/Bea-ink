# Bea-ink
Stazione meteo per display E-Paper, progettata specificamente per Venezia. Questo progetto combina dati meteo in tempo reale da OpenWeatherMap con icone meteo artistiche e una dettagliata rosa dei venti su un display E-Ink.

![Anteprima Bea-ink](Bea-ink-2.jpg)

## Caratteristiche
- Visualizzazione dati meteo in tempo reale:
  - Temperatura attuale con temperatura percepita
  - Icone meteo disegnate artisticamente
  - Informazioni dettagliate sul vento con nomi tradizionali italiani (Tramontana, Grecale, ecc.)
  - Rosa dei venti completa con indicatori direzionali
  - Dati su umidità, pressione e visibilità
  - Orari di alba e tramonto
- Sezione Cryptocurrency:
  - Prezzi in tempo reale di Bitcoin ed Ethereum
  - Variazioni percentuali nelle ultime 24 ore
- Feed notizie:
  - Ultime notizie da ANSA
  - Aggiornamento automatico ogni 5 minuti
- Icone meteo personalizzate per:
  - Sole
  - Nuvole
  - Pioggia
  - Neve
  - Temporale
  - Nebbia

## Requisiti Hardware
- Raspberry Pi (qualsiasi modello)
- Display E-Paper 7.5 pollici V2 (EPD)

## Dipendenze
- Python 3
- requests
- Pillow
- epd7in5_V2 driver

## Configurazione
Il sistema è configurato per visualizzare i dati meteo di Venezia utilizzando le API di OpenWeatherMap.

## Installazione
1. Clona il repository
2. Installa le dipendenze Python
3. Configura il crontab per l'aggiornamento automatico ogni 5 minuti

## Crediti
Creato per visualizzare le condizioni meteorologiche locali con particolare attenzione alla tradizione italiana dei nomi dei venti.
