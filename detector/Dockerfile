# Dockerfile
FROM python:3.9-slim

WORKDIR /detector
COPY detector.py /detector

RUN pip install elasticsearch

CMD ["python", "detector.py"]