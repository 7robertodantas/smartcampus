FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install requests  # necessário para registrar subscription

# Expõe porta padrão
EXPOSE 5000

# Argumentos e variáveis de ambiente
ARG APP_FILE
ENV APP_FILE=${APP_FILE}

ARG CONFIG=server
ENV CONFIG=${CONFIG}

# Copia arquivos principais
COPY fiware.py .

# Copia scripts auxiliares
COPY cronscripts/send_weather_to_orion.py ./cronscripts/
COPY crontab.txt ./cronscripts/
COPY register_subscription.py .

# Registra o crontab se necessário
RUN if [ "$CONFIG" = "cron" ]; then crontab /app/cronscripts/crontab.txt; fi

# Entrypoint condicional
CMD ["sh", "-c", "\
  if [ \"$CONFIG\" = \"server\" ]; then gunicorn --bind 0.0.0.0:5000 ${APP_FILE}:app; \
  elif [ \"$CONFIG\" = \"script\" ]; then python ${APP_FILE}.py; \
  elif [ \"$CONFIG\" = \"cron\" ]; then cron -f; \
  elif [ \"$CONFIG\" = \"subscription\" ]; then python register_subscription.py; \
  fi"]
