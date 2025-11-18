# Docker-käyttöohje

Näin ajat Streamlit-palvelun ja dokumentaation Docker-kontissa:

## 1. Rakenna Docker-image
Aja projektin juuressa:
```
docker build -t here-streamlit .
```

## 2. Käynnistä kontti
```
docker run -p 8502:8502 here-streamlit
```

- Streamlit-palvelu on nyt käytettävissä osoitteessa: http://localhost:8502
- docs-kansio on mukana kontissa (esim. dokumentaatiota varten)

## 3. Vinkkejä
- Voit muokata koodia ja rakentaa imagen uudelleen tarvittaessa.
- Jos haluat käyttää .env-tiedostoa, lisää se erikseen ja huomioi .dockerignore.
- Jos haluat pysyvän datan, käytä volumeja:
  ```
  docker run -p 8502:8502 -v $(pwd)/docs:/app/docs here-streamlit
  ```

## 4. Riippuvuudet
- Kaikki Python-riippuvuudet asennetaan uv-pakettienhallinnalla Dockerfile:n mukaisesti.

---
Lisätietoja: katso `Dockerfile` ja `docs/here_api.md`.
