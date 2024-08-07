from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid

class CustomUser(AbstractUser):
    uuid = models.UUIDField(unique=True) # pk
    email = models.EmailField(unique=True)  # 이메일 필드 추가
    user_layout = models.CharField(max_length=50)
    db_name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)
    
    
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # CustomUser에 대한 역 참조 이름
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # CustomUser에 대한 역 참조 이름
        blank=True,
        help_text='Specific permissions for this user.'
    )


class FinevoUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    # groups 필드와 user_permissions 필드에 related_name 추가
    groups = models.ManyToManyField(
        Group,
        related_name='finevouser_set',  # FinevoUser에 대한 역 참조 이름
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='finevouser_set',  # FinevoUser에 대한 역 참조 이름
        blank=True,
        help_text='Specific permissions for this user.'
    )
    