import os
from celery import Celery




os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'WebAppTG.settings')

app = Celery('WebAppTG')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()



# заносим таски в очередь
app.conf.beat_schedule = {
    'every-5-minutes': { 
        'task': 'testsite.tasks.update_currency',
        'schedule': 300.0 #crontab(minute="*/5") по умолчанию выполняет каждую минуту, очень гибко 
    },                                                              # настраивается

}
app.conf.timezone = 'Europe/Moscow'

