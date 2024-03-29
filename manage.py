#!/usr/bin/env python3
import os
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'storybook_sever.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )(exc)
    execute_from_command_line(sys.argv)
