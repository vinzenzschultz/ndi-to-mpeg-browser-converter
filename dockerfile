# Basis-Image mit Python
FROM python:3.9

# Arbeitsverzeichnis setzen
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN apt update && apt install -y libavahi-common3 libavahi-client3
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# Anwendungscode kopieren
COPY . .
COPY templates/ templates/

# Flask-Server auf Port 5000 starten
CMD ["python", "app.py"]
