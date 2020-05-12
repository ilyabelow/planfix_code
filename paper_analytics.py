#!/usr/bin/python3
# -*- coding:utf-8 -*-

#
# Обработка аналитики расхода/прихода бумаги
#

from interface import *


# Обработка аналитики бумаги. Нужно ли выносить в функцию?
def paper_workout_depr(an):
    log.info("Old value is %s, %s %s pieces of paper, new value is %s", an["Остаток входящий"], an["Баланс"],
             an['Количество'], an['Остаток'])
    # Кол-во бумаги не может быть отрицательным, если оно вышло таковым, то это человеческая вина
    if int(an['Остаток']) < 0:
        log.warning("Final amount is below zero")
        notify("Количество бумаги не может быть отрицательным!")
        return
    # id поля, содержащего резервацию бумаги на указанный в аналитике заказ (если есть)
    res_id = None
    # Новое количество бумаги в резервации
    final_res = 0
    # Если в аналитике указан заказ, то меняется соответствующая резервация
    if an["Заказ"]:
        log.info("Order is stated, working with reservations")
        p = task_get(req['id'])
        # Список из полей резерваций в задаче бумаги
        reser = get_custom_field(p, "Резерв #1", "Резерв #2", "Резерв #3")
        for r in reser:
            # Если в одном из полей (text = текст в поле) значится заказ из аналитики,
            # то обновляем это поле
            if r.find("text").string == an["Заказ"]:
                log.info("Reservation of %s was found", an["Заказ"])
                # am - поле с количеством резерва
                am = get_custom_field(p, "Количество #" + r.field.find("name").string[-1:])  # Отделение последней цифры
                log.info("Amount of reservation is %s", am.value.string)
                if an["Баланс"] == "Расход":
                    final_res = int(am.value.string) - int(an['Количество'])
                elif an["Баланс"] == "Приход":
                    final_res = int(am.value.string) + int(an['Количество'])
                else:
                    final_res = int(am.value.string)
                log.info("Final amount is %d", final_res)
                # id поля с количеством
                res_id = am.field.find("id").string
                break
        else:
            log.info("Reservation of %s wasn't found", an["Заказ"])
    # Инлекс действия
    act = req["action_link"][-7:]
    # В аналитику в действии приписывается название бумаги и остаток (НЕ НУЖНО)
    # action_update(act, ans={"id": 1870, "items": [(12120, final), (12096, req['id'])], "key": get_analytics_key(act)})
    if not res_id:
        # Обновляются поля "Остаток" и "Автор действия"
        task_update(req["id"], (740, an['Остаток']), (822, req['author']))
    else:
        # Обновляется дополнительное поле если есть резервация
        task_update(req["id"], (740, an['Остаток']), (822, req['author']), (res_id, final_res))


# Обработка аналитики бумаги. Нужно ли выносить в функцию?
def paper_workout(an):
    log.info("Old value is %s, %s %s pieces of paper, new value is %s", an["Остаток входящий"], an["Баланс"],
             an['Количество'], an['Остаток'])
    # Кол-во бумаги не может быть отрицательным, если оно вышло таковым, то это человеческая вина
    if int(an['Остаток']) < 0:
        log.warning("Final amount is below zero")
        notify("Количество бумаги не может быть отрицательным!")
        return
    # id поля, содержащего резервацию бумаги на указанный в аналитике заказ (если есть)
    res_id = None
    # Если в аналитике указан заказ, то меняется соответствующая резервация
    if an["Заказ"]:
        log.info("Order is stated, working with reservations")
        # Задача бумаги
        p = task_get(req['id'])
        # Список из полей резерваций в задаче бумаги
        reser = get_custom_field(p, "Резерв #1", "Резерв #2", "Резерв #3")
        for i in range(3):
            r = reser[i]
            # Если в одном из полей (text = текст в поле) значится заказ из аналитики,
            # то обновляем это поле
            if r.find("text").string == an["Заказ"]:
                # Проверка правильно ли указан слот
                if str(i+1) != an['Слот резервации']:
                    log.warning('The slot is stated incorrectly, requesting to redo analytics')
                    notify('В аналитике указан не тот слот! Сценарий не отработал, поэтому можете спокойно указать'
                           ' верный слот и отправить аналитику заного')
                    return
                log.info("Reservation of %s was found", an["Заказ"])
                # am - поле с количеством резерва
                am = get_custom_field(p, "Количество #" + an['Слот резервации'])
                log.info("Amount of reservation is %s, final amount is %d", an['Остаток по резервации входящий'],
                         an['Остаток по резервации'])
                # id поля с количеством
                res_id = am.field.find("id").string
                break
        else:
            log.info("Reservation of %s wasn't found", an["Заказ"])
    # Инлекс действия
    act = req["action_link"][-7:]
    # В аналитику в действии приписывается название бумаги и остаток (НЕ НУЖНО)
    # action_update(act, ans={"id": 1870, "items": [(12120, final), (12096, req['id'])], "key": get_analytics_key(act)})
    if not res_id:
        # Обновляются поля "Остаток" и "Автор действия"
        task_update(req["id"], (740, an['Остаток']), (822, req['author']))
    else:
        # Обновляется дополнительное поле если есть резервация
        task_update(req["id"], (740, an['Остаток']), (822, req['author']), (res_id, an['Остаток по резервации']))


print("Content-type: text/plain;charset=utf-8\n")
log.info("========== PAPER ANALYTICS REQUEST")

get_request(cgi.FieldStorage())

try:
    # Изъятие аналитики
    analy = parse_analytics(req["analytics"])
    if analy["name"] == "Бумага":
        paper_workout(analy)
    else:
        log.warning("Unknown analytics")
except ConnectionError:
    pass
except Exception:
    log.error("Something went wrong!", exc_info=True)