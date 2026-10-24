FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY tests ./tests
COPY scripts ./scripts
COPY bridges ./bridges
COPY artifacts/h1 ./artifacts/h1
COPY artifacts/llm_cache ./artifacts/llm_cache
COPY artifacts/s2/diag-d1g.json ./artifacts/s2/diag-d1g.json
COPY rra /usr/local/bin/rra
ENV PYTHONPATH=/app/src
# Development seeds by default; the frozen eval seeds are never the default input.
ENV RRA_SEED_FILE=/app/config/dev_seeds.json

CMD ["rra", "bench", "--output-dir", "/tmp/rra-out"]
