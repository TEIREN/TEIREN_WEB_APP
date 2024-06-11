FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y openssh-client
RUN apt-get update && apt-get install -y ssh

# start.sh 스크립트 파일을 이미지에 복사
COPY start.sh /app/start.sh
# 스크립트 파일에 실행 권한 부여
RUN chmod +x /app/start.sh

# 필요한 경우, 다른 파일들에 대해서도 여기서 권한을 설정할 수 있습니다.
# 예: RUN chmod 600 /app/어떤_중요한_파일

COPY . .

# CMD 대신 start.sh 스크립트를 사용
CMD ["/app/start.sh"]