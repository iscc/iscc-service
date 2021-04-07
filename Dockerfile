FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

ENV ISCC_SERVICE_ALLOWED_ORIGINS="*"
ENV MODULE_NAME=iscc_service.main
ENV PORT=8080
ENV LOG_LEVEL=info
ENV TIMEOUT=3600

RUN apt-get update && apt-get install -y --no-install-recommends openjdk-11-jre-headless curl && \
    pip install --upgrade pip && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && \
    rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml /app/
RUN poetry install --no-root --no-dev -vvv

COPY iscc_service /app/iscc_service
