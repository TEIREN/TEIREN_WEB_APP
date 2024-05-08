from custom.storage.customstorage import CleanFileNameStorage

from django.db import models
from django.utils.text import slugify


def evidence_directory_path(instance, filename):
    return f'{instance.user_uuid}/Evidence/{slugify(instance.product)}/{filename}'

def policy_directory_path(instance, filename):
    return f'{instance.user_uuid}/Policy/{filename}'

def asset_directory_path(instance, filename):
    return f'{instance.user_uuid}/Asset/{filename}'

class Evidence(models.Model):
    user_uuid = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    product = models.CharField(max_length=500)
    uploadedFile = models.FileField(upload_to=evidence_directory_path, 
                                    storage=CleanFileNameStorage())
    dateTimeOfUpload = models.DateTimeField(auto_now=True)


class Policy(models.Model):
    user_uuid = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    uploadedFile = models.FileField(upload_to=policy_directory_path,
                                    storage=CleanFileNameStorage())
    dateTimeOfUpload = models.DateTimeField(auto_now=True)


class Asset(models.Model):
    user_uuid = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    uploadedFile = models.FileField(upload_to=asset_directory_path,
                                    storage=CleanFileNameStorage()) # /
    dateTimeOfUpload = models.DateTimeField(auto_now=True)