from django.db import models

MAX_CYPHER_SIZE = 9999
MAX_TYPE_SIZE = 100

class Cypher(models.Model):
    function_name = models.CharField(max_length=MAX_TYPE_SIZE, default='')
    cypher_type = models.CharField(max_length=MAX_TYPE_SIZE, default='')
    cypher = models.TextField(max_length=MAX_CYPHER_SIZE, default='')

class ApiCypher(models.Model):
    cypher_type = models.CharField(max_length=MAX_TYPE_SIZE, default='')
    cypher = models.TextField(max_length=MAX_CYPHER_SIZE, default='')