FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
# Is based on python:3.7 which is python:3.7.x-buster -> Debian Buster

ARG POETRY_VERSION=1.0.0
ENV GUNICORN_WORKERS=4
ENV ALLOWED_ORIGINS="*"
ENV ISCC_STREAM="iscc"
ENV NODE_IP="127.0.0.1"
ENV NODE_PORT="9718"
ENV NODE_USER=""
ENV NODE_PWD=""


# libchromaprint-tools not needed, iscc-cli uses a locally downloaded (-> iscc init) version of fpcalc
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-11-jre-headless \
 && pip install --upgrade pip \
 && pip install "poetry==$POETRY_VERSION" \
 && rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false \
 && poetry install --no-dev --no-ansi --no-interaction \
 && iscc init # Call iscc-cli init to let it take care of it's dependencies

COPY iscc_service /app/iscc_service

EXPOSE 8080

CMD exec gunicorn iscc_service.main:app -b 0.0.0.0:8080 -w ${GUNICORN_WORKERS} -k uvicorn.workers.UvicornWorker
