import ipaddress
import os

from dotenv import load_dotenv

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

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

SHA_KEY = os.environ.get('SHA_KEY').encode()
SALT = os.environ.get('SALT').encode()

GREEN_SMS_TOKEN = os.environ.get('GREEN_SMS_TOKEN')
TEST_SMS_CODE = os.environ.get('TEST_SMS_CODE')

SHOP_ID = os.environ.get('SHOP_ID')
SHOP_KEY = os.environ.get('SHOP_KEY')

ORIGINS = os.environ.get('ORIGINS').split(' ')

REFRESH_TTL_DAYS = 30
ACCESS_TTL_MINUTES = 15

DEFAULT_PHONE = '79123456789'

YOOKASSA_NETWORKS = [
    ipaddress.ip_network('185.71.76.0/27'),
    ipaddress.ip_network('185.71.77.0/27'),
    ipaddress.ip_network('77.75.153.0/25'),
    ipaddress.ip_network('77.75.154.128/25'),
    ipaddress.ip_network('2a02:5180::/32'),
    ipaddress.ip_network('77.75.156.11'),
    ipaddress.ip_network('77.75.156.35'),
]
