from django.test import TestCase

# Create your tests here.
from common.common import get_uuid

from datetime import datetime
import time

# from manager.models import User

timestamp = int(time.time())
print(timestamp)
dt = datetime.fromtimestamp(1562302878.1321234324)
print(dt)
dt2 = datetime(dt.year, dt.month, 12, 22, 12, 23, 0)
print(dt2 - dt)

# User.objects.filter(createTime__gte=)

uuid = get_uuid()
print(uuid)

a = 10
if True:
    a = 3
print(a)