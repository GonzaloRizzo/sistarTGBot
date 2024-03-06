FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

RUN apt-get update && apt-get -y install cron

RUN pip install --no-cache-dir poetry==1.2.2

WORKDIR /src

COPY poetry.lock pyproject.toml /src/

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY . /src

RUN echo '*/30 * * * * cd /src && python main.py >/proc/1/fd/1 2>/proc/1/fd/2' | crontab
CMD printenv > /etc/environment && cron -f
