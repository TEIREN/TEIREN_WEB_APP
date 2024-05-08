from django.db import models
from django.utils.text import slugify
import os

class Document(models.Model):
    title = models.CharField(max_length=200)
    uploadedFile = models.FileField(upload_to="result/")
    dateTimeOfUpload = models.DateTimeField(auto_now=True)

# Define a function for the upload_to parameter
def evidence_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/evidence/<product>/<filename>
    # Use slugify to convert the product name to a URL-friendly format
    print(slugify(instance.product))
    print(filename)
    return f'evidence/{slugify(instance.product)}/{filename}'

class Evidence(models.Model):
    title = models.CharField(max_length=200)
    product = models.CharField(max_length=500)
    uploadedFile = models.FileField(upload_to=evidence_directory_path)
    dateTimeOfUpload = models.DateTimeField(auto_now=True)

class Policy(models.Model):
    title = models.CharField(max_length=200)
    uploadedFile = models.FileField(upload_to=f"policy/")
    dateTimeOfUpload = models.DateTimeField(auto_now=True)

class Asset(models.Model):
    title = models.CharField(max_length=200)
    uploadedFile = models.FileField(upload_to=f"asset/")
    dateTimeOfUpload = models.DateTimeField(auto_now=True)
