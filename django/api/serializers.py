from rest_framework import serializers
from .models import Cypher, ApiCypher

class CypherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cypher
        fields = '__all__'


class ApiCypherSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiCypher
        fields = '__all__'