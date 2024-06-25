from rest_framework import serializers
from .models import Metrics

class MetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metrics
        fields = '__all__'