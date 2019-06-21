from django.test import TestCase

# Create your tests here.
from common.common import get_uuid

uuid = get_uuid()
print(uuid)
