import os

from dotenv import load_dotenv

class MyToken:
    TOKEN: str

load_dotenv()

MY_TOKEN = MyToken()
MY_TOKEN.TOKEN = os.environ.get('BOT_TOKEN')
