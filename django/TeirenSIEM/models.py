from django.db import models

# Create your models here.

class GridLayout(models.Model):
    name = models.CharField(max_length=100)
    data = models.CharField(max_length=100000)
    isDefault = models.BooleanField(default=False)