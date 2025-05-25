FROM python:3.10-slim

WORKDIR /app

# ./entities
COPY entities/ ./entities/
COPY create_entities.py .
COPY weather_simulator.py .

RUN pip install --no-cache-dir requests

CMD ["sh", "-c", "python create_entities.py && python weather_simulator.py"]
