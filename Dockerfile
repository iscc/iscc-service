FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
# Is based on python:3.7 which is python:3.7.x-buster -> Debian Buster

ARG POETRY_VERSION=1.1.4
ENV GUNICORN_WORKERS=1
ENV ALLOWED_ORIGINS="*"


# libchromaprint-tools not needed, iscc-cli uses a locally downloaded (-> iscc init) version of fpcalc
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-11-jre-headless \
 && pip install --upgrade pip \
 && pip install "poetry==$POETRY_VERSION" \
 && rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml /app/

RUN poetry install --no-dev --no-ansi --no-interaction \
 && poetry run iscc-service-init

COPY iscc_service /app/iscc_service

EXPOSE 8080

CMD exec gunicorn iscc_service.main:app -b 0.0.0.0:8080 -w ${GUNICORN_WORKERS} -k uvicorn.workers.UvicornWorker
