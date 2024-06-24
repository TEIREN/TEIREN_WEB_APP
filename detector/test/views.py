from django.db import models
from django.shortcuts import render
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .detector import check_logs
from .input_ruleset import create_ruleset

# 모델 정의
class Ruleset(models.Model):
    name = models.CharField(max_length=100)
    system = models.CharField(max_length=50)
    severity = models.IntegerField()
    query = models.JSONField()

    def __str__(self):
        return self.name

# 시리얼라이저 정의
class RulesetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruleset
        fields = '__all__'

# 룰셋 생성 엔드포인트
@api_view(['POST'])
def create_ruleset_view(request):
    serializer = RulesetSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        system = request.data.get('system')
        create_ruleset(system, serializer.data)  # input_ruleset.py의 함수 호출
        return Response({"message": "Ruleset created successfully."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 로그 확인 엔드포인트
@api_view(['GET'])
def check_logs_view(request, system):
    try:
        check_logs(system)  # detector.py의 함수 호출
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except ConnectionError as e:
        return Response({"error": f"Connection error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": f"An error occurred: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({"message": "Logs checked successfully."}, status=status.HTTP_200_OK)
