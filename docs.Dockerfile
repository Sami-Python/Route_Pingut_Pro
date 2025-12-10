FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY docs/doc-requirements.txt .
RUN pip install uv
RUN uv pip install --no-cache-dir --system -r doc-requirements.txt

# Copy configuration and documentation
COPY docs/mkdocs.yml .
COPY docs/docs/ docs/

# Expose the default MkDocs port
EXPOSE 8000

# Serve the documentation
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000"]
