import hashlib
import hmac
import base64
import requests
import time

def make_signature(timestamp, access_key, secret_key, uri):
    secret_key = bytes(secret_key, 'UTF-8')

    method = "POST"
    uri = uri

    message = method + " " + uri + "\n" + timestamp + "\n" + access_key
    message = bytes(message, 'UTF-8')
    signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
    return signingKey


def CloudActivityTracer(access_key, secret_key):
    # unix timestamp 설정
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)

    # API 서버 정보
    server = "https://cloudactivitytracer.apigw.ntruss.com"

    # API URL 예시 : 상품별 가격 리스트 호출 api
    uri = "/api/v1/activities"

    # http 호출 헤더값 설정
    http_header = {
        'Content-Type': 'application/json; charset=utf-8',
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': make_signature(timestamp, access_key, secret_key, uri)
    }
    body = {}

    # api 호출
    response = requests.post(server + uri, headers=http_header, json=body)

    try:    #키가 없을 때
        response.json()['error']
        return False
    except KeyError:    #키가 있을 때
        return True