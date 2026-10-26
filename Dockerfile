FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY config ./config
COPY rra /usr/local/bin/rra
ENV PYTHONPATH=/app/src

CMD ["rra", "run", "--scenario", "bias", "--seed", "7", "--compensation", "on", "--output-dir", "/tmp/rra-demo"]
