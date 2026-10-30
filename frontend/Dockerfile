# Container voor de frontend: het dashboard (HTML, CSS en JavaScript).

# Basis: dezelfde kleine Python-versie als de backend.
FROM python:3.13-slim

WORKDIR /app

# De bestanden van het dashboard kopiëren.
COPY index.html styles.css ./

# Python heeft een ingebouwde webserver die de bestanden in deze map serveert.
# Het dashboard is daarna bereikbaar op poort 8080.
EXPOSE 8080
CMD ["python", "-m", "http.server", "8080"]
