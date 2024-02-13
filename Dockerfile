FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy


RUN pip install --no-cache-dir poetry==1.2.2

WORKDIR /src

COPY poetry.lock pyproject.toml /src/

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY . /src

CMD python main.py
