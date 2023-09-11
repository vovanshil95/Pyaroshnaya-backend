import datetime
import os
import subprocess

from celery import Celery
from celery.schedules import crontab

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

celery_app = Celery('tasks', broker='redis://localhost:6379')

celery_app.conf.broker_connection_retry_on_startup = True

path = '../backups'

@celery_app.task()
def copy_psql_db():
    [os.remove(os.path.join(path, file_)) for file_ in os.listdir(path) if os.path.isfile(os.path.join(path, file_))]
    day = datetime.datetime.now().strftime('%Y-%m-%d')
    with open(os.path.join(path, f'{day}.sql'), 'w') as f:
        subprocess.run(['pg_dump',
                            '-h', f'{DB_HOST}',
                            '-p', f'{DB_PORT}',
                            '-U', f'{DB_USER}',
                            f'{DB_NAME}'],
                           env={'PGPASSWORD': DB_PASS},
                           stdout=f)
        subprocess.run(['git', 'add', '.'], cwd=path)
        subprocess.run(['git', 'commit', '-m', '"update db backup"'], cwd=path)
        subprocess.run(['git', 'push'], cwd=path)

celery_app.conf.beat_schedule = {
    'run_every_day_at_4am': {
        'task': 'tasks.tasks.copy_psql_db',
        'schedule': crontab(hour=4, minute=0),
        'args': (),
    },
}

celery_app.conf.timezone = 'Europe/Moscow'
