# iscc-service - ISCC Web Service API
[![Version](https://img.shields.io/pypi/v/iscc-service.svg)](https://pypi.python.org/pypi/iscc-service/)
[![Downloads](https://pepy.tech/badge/iscc-service)](https://pepy.tech/project/iscc-service)
[![Pulls](https://shields.beevelop.com/docker/pulls/titusz/iscc-service.svg?style=flat-square)](https://hub.docker.com/r/titusz/iscc-service)

> A REST OpenAPI Backend for creating [**ISCC codes**](https://iscc.codes) for digital media files.


**Note**: This is work in progress. Use with care and at your own risk

The Webservice is build with [FastAPI](https://github.com/tiangolo/fastapi) and makes
use of the [ISCC reference implementation](<https://github.com/iscc/iscc-specs>) and
the [ISCC Command Line Tool](https://github.com/iscc/iscc-cli) and includes an
interactive API documentation:

![Interactive ISCC Api Docs](screenshot.jpg)


The Docker image is published at https://hub.docker.com/r/titusz/iscc-service


## Setup for development

If you are using [poetry](https://python-poetry.org/):

- After checkout cd into code directory and run 'poetry install' to install dependencies.
- Launch dev server with: 'uvicorn iscc_service.main:app --reload'
- See API docs at: http://127.0.0.1:8000

For the 'lookup' endpoint to work you must provide env variables for node connection.
See [config.py](iscc_service/config.py)

## Install via pip

```bash
$ pip3 install iscc-service
```

Run webservice via uvicorn

```bash
$ isccservice
INFO:     Started server process [18800]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Publishing on Docker HUB:

```bash
docker login
docker build -t iscc-service -f Dockerfile .
docker run --rm -p 8080:8080 -it iscc-service
docker tag iscc-service username/iscc-service:0.1.9
docker push username/iscc-service:0.1.9
```

## Change Log

### [0.2.0] - 2020-05-01
- Update to support flac and opus audio files

### [0.1.9] - 2020-04-27

- Support updated Content-ID Audio
- Support incomplete ISCC codes
- Updated dependencies

### [0.1.8] - 2020-03-02

- Add support for mobi files
- Initial pypi release


## License

MIT © 2019-2020 Titusz Pan
