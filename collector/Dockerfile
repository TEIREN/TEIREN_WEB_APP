FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y ssh sudo curl apt-transport-https gnupg systemd rsyslog libgpm2 libncurses6 libyaml-0-2

# Fluentd 설치 및 설정
RUN curl -L https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-fluent-package5.sh | sh

COPY . .

# Fluentd 설정 파일 복사
COPY fluentd.conf /etc/fluent/fluentd.conf

EXPOSE 8000 5140

# setup_linux.sh 스크립트를 실행하도록 설정
COPY setup_linux.sh /app/setup_linux.sh
RUN chmod +x /app/setup_linux.sh

CMD ["/app/start.sh"]
