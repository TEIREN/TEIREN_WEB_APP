FROM python:3.8

WORKDIR /app

COPY requirements.txt /app/
COPY entrypoint.sh /app/

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh

CMD ["entrypoint.sh"]