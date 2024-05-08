FROM python:3.11.9-bookworm

WORKDIR /app

COPY requirements.txt .
COPY run.sh .

RUN apt-get -y update \
    && apt-get -y install libpq-dev python3-dev \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["/bin/bash", "/app/run.sh"]