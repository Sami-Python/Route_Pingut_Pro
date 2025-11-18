# Streamlit + docs Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Kopioi koodi ja docs
COPY . /app

# Asenna riippuvuudet uv:llä
RUN pip install --upgrade pip && pip install uv
RUN uv pip install --system -r requirements.txt

# Streamlit portti 8502
EXPOSE 8502

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.headless=true"]
