# Container voor de backend: de API in Python (FastAPI).

# Basis: een kleine Linux-versie waar Python al op staat.
FROM python:3.13-slim

# Alle commando's hieronder gebeuren in de map /app in de container.
WORKDIR /app

# Eerst alleen requirements.txt kopiëren en de pakketten installeren.
# Docker onthoudt elke stap: zolang requirements.txt niet verandert,
# slaat hij deze stap bij een volgende build over. Dat gaat sneller.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Daarna de code en de data. Wat niet mee moet, staat in .dockerignore.
COPY . .

# De API starten op poort 8000, net zoals je het lokaal doet.
# --host 0.0.0.0 zorgt dat de API ook van buiten de container bereikbaar is.
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
