"""
Django settings for service project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-76dtlqs!mq_1(mxvkd@ep-)9!sk=e4(u(7^hy&c%2bqw5iepev'
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']
# REST API DRF SETTINGS #
from rest_framework import permissions

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework_api_key.permissions.HasAPIKey",
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365*100),  # 토큰 유효 기간을 매우 길게 설정 (예: 100년)
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=365*100),  # 갱신 시간도 동일하게 설정
    'SLIDING_TOKEN_LIFETIME': timedelta(days=365*100),  # 최대 유효 기간도 동일하게 설정
    'SLIDING_TOKEN_REFRESH_LIFETIME_ALTERNATIVE': timedelta(days=365*100),
    'SLIDING_TOKEN_LIFETIME_ALTERNATIVE': timedelta(days=365*100),
}

# DJOSER Settings
DJOSER = {
    'SERIALIZERS': {
        'user_create': 'api.serializers.CustomUserCreateSerializer',  # 회원가입 시 사용할 Serializer 지정
    },
}

# Application definition
INSTALLED_APPS = [
    '_auth',
    'api.metrics',
    'api.trigger',
    'common',
    'M_logs',
    'M_equipments',
    'M_threatD',
    'configurations',
    'dashboard',
    'compliance',
    'testing',
    'monitoring',
    "rest_framework",
    "rest_framework_api_key",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites', # 여러 사이트 동시 운영
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework_simplejwt', # rest framework jwt token
    # "debug_toolbar",
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
]
# INTERNAL_IPS = [
#     # ...
#     '127.0.0.1',
#     # ...
# ]
AUTHENTICATION_BACKENDS = {
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
}

ROOT_URLCONF = 'service.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'service.wsgi.application'
# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
MONGODB = {
    'HOST': '223.130.139.109',  # MongoDB server address
    'PORT': 27018,  # MongoDB server port
    'USERNAME': 'mongo',  # MongoDB username
    'PASSWORD': 'pY_PjwLgED8v3C7XrEE8TXo',  # MongoDB password
    'ADMIN': 'ts_config',
    'TEST': 'test',
    'LOCAL': 'local'
}

NEO4J = {
    'HOST': '3.36.151.254',
    'PORT': '7687',
    'USERNAME': 'neo4j',
    'PASSWORD': 'yuw0n!sjj@ng'
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
USE_L10N = True
# Login URL
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session Age (3600sec. = 1hr)
SESSION_COOKIE_AGE = 3600
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_ROOT = '/staticfiles/'
STATIC_URL = '/staticfiles/'
STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles',
    os.path.join(BASE_DIR, 'staticfiles')
]
# Neo4j
# NEO4J_HOST = '223.130.139.109'
# NEO4J_PORT = '7688'
# NEO4J_USERNAME = 'neo4j'
# NEO4J_PASSWORD = 'pY_PjwLgED8v3C7XrEE8TXo'
# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'chosomang12@teiren.io'
# EMAIL_HOST_PASSWORD = 'ymdriofeqgmuuqst'

EMAIL_HOST_USER = 'yoonan@teiren.io'
EMAIL_HOST_PASSWORD = 'djlwlkxhgrprtesj'


############# OPTIONS ###############

# Email confirm
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'email_confirm_done'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'email_confirm_done'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
# ACCOUNT_EMAIL_VARIFICATION = 'optional'

# Auth, Register
ACCOUNT_PASSWORD_INPUT_RENDER_VALUE = True

### DATABASE ###
AUTH_USER_MODEL = '_auth.CustomUser'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = os.path.join('/home/yoonan/DATABASE/')
MEDIA_URL = '/media/'
# APPEND_SLASH = True

DEFAULT_FILE_STORAGE = 'custom.storage.customstorage.CleanFileNameStorage'