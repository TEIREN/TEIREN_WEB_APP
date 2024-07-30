FROM python:3.8

WORKDIR /app

COPY requirements.txt /app/
COPY entrypoint.sh /app/

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh

RUN apt-get update \
    && apt-get install -y wkhtmltopdf \
    && apt-get -y install xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y poppler-utils

CMD ["entrypoint.sh"]