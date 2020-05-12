#!/usr/bin/python3
# -*- coding:utf-8 -*-

#
# Обработка аналитики в задаче с процессом
#

from interface import *
from math import ceil

# Обработка аналитики бумаги. Нужно ли выносить в функцию?
def process_workout(an):
    name = an['Справочник']
    time = ceil(float(an['Время работы в минутах'].replace(',','.')))
    log.info('New name will be %s, new duration will be %d',name,time)
    task_update(req['id'], duration=time, name=name)


print("Content-type: text/plain;charset=utf-8\n")
log.info("========== PROCESS ANALYTICS REQUEST")

get_request(cgi.FieldStorage())

try:
    # Изъятие аналитики
    analy = parse_analytics(req["analytics"])
    if analy['name'] == 'Время изготовления':
        process_workout(analy)
except ConnectionError:
    pass
except Exception:
    log.error("Something went wrong!", exc_info=True)

remove_blocker(req["id"])
