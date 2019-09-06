# coding: utf-8
"""
Django settings for storybook_sever project.

Generated by 'django-admin startproject' using Django 2.1.8.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from storybook_sever.config import version

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'q!#xy1-uo4)^o5lg^58bpf69ss5g&9w0xv%e#e&1)+ycnr1s@%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    '192.168.100.201',
    '192.168.100.166',
    '192.168.100.253',
    '192.168.100.252',
    '192.168.100.235',
    '192.168.100.199'
]

REDIS_TIMEOUT = 7 * 24 * 60 * 60
CUBES_REDIS_TIMEOUT = 60 * 60
NEVER_REDIS_TIMEOUT = 365 * 24 * 60 * 60

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'api',
    'manager',
    'public',
    'djcelery',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 跨域相关中间件
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'storybook_sever.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'storybook_sever.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

if version == 'debug':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
            'NAME': 'htdb',  # 储数据的库名
            'USER': 'root',  # 数据库用户名
            'PASSWORD': 'hbb123',  # 密码
            'HOST': '127.0.0.1',  # 主机
            'PORT': '3306',  # 数据库使用的端口
            'OPTIONS': {
                    'charset': 'utf8mb4',
                    'use_unicode': True, },
            # 'TIME_ZONE': 'Asia/Shanghai'
        }
    }
    # 缓存配置
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                'redis://127.0.0.1:6379/0',
            ],  # redis服务ip和端口，
            'KEY_PREFIX': 'manage',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 1024,
                }
            },
        },
        'api': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                'redis://127.0.0.1:6379/1',
            ],  # redis服务ip和端口，
            'KEY_PREFIX': 'api',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 512,
                }
            },
        },
    }
elif version == 'test':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
            'NAME': 'htdb',  # 储数据的库名
            'USER': 'root',  # 数据库用户名
            'PASSWORD': 'hbb123',  # 密码
            'HOST': '192.168.100.235',  # 主机
            'PORT': '3306',  # 数据库使用的端口
            'OPTIONS': {
                    'charset': 'utf8mb4',
                    'use_unicode': True, },
            # 'TIME_ZONE': 'Asia/Shanghai'
        }
    }
    # 缓存配置
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                'redis://127.0.0.1:6379/0',
            ],  # redis服务ip和端口，
            'KEY_PREFIX': 'manage',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 1024,
                }
            },
        },
        'api': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                'redis://127.0.0.1:6379/1',
            ],  # redis服务ip和端口，
            'KEY_PREFIX': 'api',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 512,
                }
            },
        },
    }

elif version == 'ali_test':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
            'NAME': 'htdb',  # 储数据的库名
            'USER': 'root',  # 数据库用户名
            'PASSWORD': 'hbb123',  # 密码
            'HOST': '39.97.233.65',  # 主机
            'PORT': '8002',  # 数据库使用的端口
            'TIME_ZONE': 'Asia/Shanghai',
            'OPTIONS': {
                    'charset': 'utf8mb4',
                    'use_unicode': True, },
        }
    }
    # 缓存配置
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                'redis://172.18.0.5:6379/0',
            ],  # redis服务ip和端口，
            'KEY_PREFIX': 'manage',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 1024,
                },
                'PASSWORD': 'hbb123',
            },
        },
        'api': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                'redis://172.18.0.5:6379/1',
            ],  # redis服务ip和端口，
            'KEY_PREFIX': 'api',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 512,
                },
                'PASSWORD': 'hbb123',
            },
        },
    }

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'django.db.backends': {
#             'handlers': ['console'],
#             'propagate': True,
#             'level': 'DEBUG',
#         },
#     }
# }




LOGGING = {
    'version': 1,
    # 是否禁用已经存在的日志器
    'disable_existing_loggers': False,
    # 日志格式化器
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(module)s.%(funcName)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        # 详细
        'verbose': {
            'format': '%(asctime)s %(levelname)s [%(process)d-%(threadName)s] '
                      '%(module)s.%(funcName)s line %(lineno)d: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'filters': {
        # 只有在Django配置文件中DEBUG值为True时才起作用
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        # 输出到控制台
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'formatter': 'simple',
        },
        # 输出到文件(每周切割一次)
        'file1': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'access.log',
            'when': 'W0',
            'backupCount': 12,              #备份份数
            'formatter': 'simple',          #使用哪种formatters日志格式
            'level': 'DEBUG',
        },
        # 输出到文件(每天切割一次)
        'file2': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'error.log',
            'when': 'D',
            'backupCount': 31,
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        # 输出到文件(每周切割一次) -- 用户访问IP和访问的路径
        'file3': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'ipandpath.log',
            'when': 'W0',
            'backupCount': 12,              #备份份数
            'formatter': 'simple',          #使用哪种formatters日志格式
            'level': 'INFO',
        },
    },
    # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTEST
    'loggers': {
        'django': {
            # 需要使用的日志处理器
            'handlers': ['console', 'file1', 'file2'],
            # 是否向上传播日志信息
            'propagate': True,
            'level': 'DEBUG',
        },
        'ipandpath': {
            # 需要使用的日志处理器
            'handlers': ['file3'],
            # 是否向上传播日志信息
            'propagate': False,
            'level': 'INFO',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

DEFAULT_CHARSET = "UTF-8"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

# 跨域攻击配置
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = (
    'http://screentest.hbbclub.com',
    'http://shoptest.hbbclub.com'
)
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)
CORS_ALLOW_HEADERS = (
    'Content-Type',
    'token',
    'Content-Length',
    'Accept-Encoding',
    'X-CSRF-Token',
    'Authorization',
    'accept',
    'origin',
    'Cache-Control',
    'X-Requested-With',
    'XSRF-TOKEN',
    'X-XSRF-TOKEN'
)

REST_FRAMEWORK = {
    # 分页配置
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 1,
    # 过滤
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    # 重构renderer
    'DEFAULT_RENDERER_CLASSES': (
        'utils.renderer.MyJsonRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'manager.auths.CustomAuthentication',
    ),
    # 配置默认的授权类
    'DEFAULT_PERMISSION_CLASSES': (
        'manager.auths.CustomAuthorization',
    ),
    'EXCEPTION_HANDLER': 'utils.custom_exceptions.custom_exception_handler'
}


# Celery settings
CELERY_BEAT_SCHEDULER  = 'django_celery_beat.schedulers.DatabaseScheduler'
BROKER_URL = 'redis://127.0.0.1:6379/'
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/'
if version == "ali_test":
    BROKER_URL = 'redis://172.18.0.5:6379/'
    CELERY_BROKER_URL = 'redis://172.18.0.5:6379/'
CELERY_RESULT_BACKEND = 'redis://172.17.118.207:6379/2'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_ENABLE_UTC = False
# CELERY_TIMEZONE = TIME_ZONE
DJANGO_CELERY_BEAT_TZ_AWARE = False
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


