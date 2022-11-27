FROM python:3.10.8-alpine3.16


RUN apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev \
    && pip install --no-cache-dir poetry==1.2.2

WORKDIR /src

COPY poetry.lock pyproject.toml /src/

RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

COPY . /src

CMD python main.py
