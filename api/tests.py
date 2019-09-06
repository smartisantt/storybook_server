from django.test import TestCase

# Create your tests here.
from common.taskMQ import audioWorker

if __name__ == "__main__":
    uuid = "E2090F1A7AC14CD79D41AA5DAF43C8D5"
    audioWorker.delay(uuid, 1)
