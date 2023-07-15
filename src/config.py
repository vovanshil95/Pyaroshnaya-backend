from dotenv import load_dotenv

import os

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

TEST_DB_HOST = os.environ.get('TEST_DB_HOST')
TEST_DB_PORT = os.environ.get('TEST_DB_PORT')
TEST_DB_NAME = os.environ.get('TEST_DB_NAME')
TEST_DB_USER = os.environ.get('TEST_DB_USER')
TEST_DB_PASS = os.environ.get('TEST_DB_PASS')

SHA_KEY = os.environ.get('SHA_KEY').encode()

REFRESH_TTL_DAYS = 30
ACCESS_TTL_MINUTES = 15

GREEN_SMS_TOKEN = os.environ.get('GREEN_SMS_TOKEN')

ORIGINS = os.environ.get('ORIGINS').split(' ')
