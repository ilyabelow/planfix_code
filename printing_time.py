#!/usr/bin/python3
# -*- coding:utf-8 -*-

#
# Подсчёт времени печати заказа
#

from interface import *
from math import ceil
from time import sleep


def get_start_time():
    if req['machine'] == 'PM-52':
        time = get_handbook_field(get_record(10, 70), 4970).value.string
    else:
        time = get_handbook_field(get_record(10, 71), 4970).value.string

    try:
        return int(time[0:2])*60 + int(time[3:5])
    except TypeError:
        log.warning("Invalid info format")
        notify("Неверный формат данных в справочнике о времени приладки")
        return

# Вычисление времени печати
def printing_time():
    if "info" not in req:
        log.warning("Info not stated")
        notify("Не указана информация о количестве печатных листов!")
        return
    log.debug("Info:", req["info"])
    # В строке времени находится через пробел инфа о нескольких печатных листах
    lists = req["info"].split()
    times = []
    total = 0
    try:
        for l in lists:
            # n - количество печатных листов, x - тираж; разделяются *
            n, x = (int(a) for a in l.split(sep="*"))
            # Время прикладки (?) разное в зависимости от машин
            # if req["machine"] == "PM-52":
            #     prep_time = 1/3  # Для PM-52 - 20 минут
            # else:
            #     prep_time = 2/3  # Для PM-74 - 40 минут
            t = get_start_time() + ceil(60 * x / 7000)
            total += t*n*2
            log.debug('For %s time is %f', l, t)
            h = t//60  # Часы
            m = t - h*60  # Минуты
            time = str(h) + "ч" + str(m) + "м"  # Красивое время
            log.debug("In hours and minutes: %s", time)
            times.append(str(n * 2) + "*" + time)  # n * 2 - потому что у листа две стороны
    except ValueError:
        log.warning("Invalid info format")
        notify("Неверный формат данных о количестве печатных листов!")
        return
    total = int(ceil(total*1.2))
    beat_time = " ".join(times) + ' Всего: '+str(total)
    log.info("Final time: %s", beat_time)
    log.debug('Updating task...')
    if req['action'] == 'print_time':
        task_update(req["id"], (880, beat_time))
    else:
        task_update(req["id"], duration=total)


print("Content-type: text/plain;charset=utf-8\n")

sleep(3)

log.info("========== PRINTING TIME REQUEST")

get_request(cgi.FieldStorage())

try:
    printing_time()
except ConnectionError:
    pass
except Exception:
    log.error("Something went wrong!", exc_info=True)
