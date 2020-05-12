#!/usr/bin/python3
# -*- coding:utf-8 -*-

#
#
#

from interface import *


def edit_shift():
    # Номер действия, в котором содержится нужная аналитика
    act = req['action_link'][-7:]
    log.info('Action id ' + act)
    # Ключ аналитики
    key = get_analytics_key(act)
    log.info('An key ' + key)

    # В аналитике изменяется время
    log.info('Analitics updating...')

    action_update(act, ans={"id": 1858, "items": [(12190, "<begin>0:00</begin><end>3:00</end>")], "key": key})
    # усё!


print("Content-type: text/plain;charset=utf-8\n")
log.info("========== SHIFT ANALITICS REQUEST")
get_request(cgi.FieldStorage())

try:
    edit_shift()
except ConnectionError:
    pass
except Exception:
    log.error("Something went wrong!", exc_info=True)

remove_blocker(req["id"])
