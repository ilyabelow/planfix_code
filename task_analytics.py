#!/usr/bin/python3
# -*- coding:utf-8 -*-

#
# Обработка аналитик, добавляемых в задачи заказа
#

from interface import *

# Когда будет високосный год - изменю вручную
months = 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31


# Разбивает промежуток времени на кусочки в зависимости от введённых перерывов
# Перерыв - пара время начала [0] и время конца [1] перерыва в минутах (всё в минутах)
# date - номер дня в году
def plan_forward(date, begin, dur, breaks):
    periods = []
    while dur > 0:
        # Рассматриваются все перерывы по порядку
        for b in breaks:
            # Если начало промежутка времени находится после начала текущего рассматриваемого перерыва
            if begin >= b[0]:
                # Если начало находится во время перерыва, то начало устанавливается на конец перерыва
                if begin <= b[1]:
                    begin = b[1]
                # Переход к следующему перерыву
                continue
            else:
                # Подсчёт времени между началом промежутка времени и перерывом
                diff = b[0] - begin
                # Если времени, которое необходимо распределить, меньше чем времени до следующего перерыва
                if dur <= diff:
                    # То конец отрезка устанавливается так, всё время мы распределили
                    end = begin + dur
                    dur = 0
                else:
                    # Иначе конец отрезка устанавливается в начало перерыва.
                    end = b[0]
                    dur -= diff

            periods.append([date, begin, end])
            # Конец перерыва устанавливается как начало следующего участка времени
            begin = b[1]
            # Переход через ночь
            if b[1] < b[0]:
                date += 1
            # Выход происходит из цикла с перерывами, а не из while!
            if dur == 0:
                break
    return periods


# Перевод минут и дней в читаемый формат времени и даты
def translator(periods, year):
    per = []
    for p in periods:
        # Перевод минут в чч:мм
        m = p[1] % 60
        if m < 10:
            m = '0' + str(m)
        else:
            m = str(m)
        begin = str(p[1] // 60) + ':' + m

        m = p[2] % 60
        if m < 10:
            m = '0' + str(m)
        else:
            m = str(m)
        end = str(p[2] // 60) + ':' + m
        # Определение месяца (переход между годами не работает, ну нафиг его)
        days = p[0]
        mon = 1
        for m in months:
            # Количество дней вычитается оставшиеся дни не уместятся в одном месяце
            if days <= m:
                break
            mon += 1
            days -= m
        per.append(['{0}-{1}-{2}'.format(days, mon, year), begin, end])
    return per


# Разбивает аналитику "Планируемое время работы" на несколько, вставляя перерывы, а так же меняет машину
def plans_workout(an):
    if 'printing_time' not in req:
        log.warning('Printing time is not stated')
        notify('Не указано время печати! (оригинальная аналитика не удалена)')
        return
    # Номер действия, в котором содержится нужная аналитика
    act = req['action_link'][-7:]
    # Ключ аналитики. Считываться будет только первый ключ!
    key = get_analytics_key(act)
    log.debug('Deleting original analytics...')
    # Полное удаление старой аналитики
    action_update(act, deleted_key=key)

    # Обработка аналитики для печатных машин

    # TODO СРОЧНО убрать это после того, как общая продолжительность будет где положено
    pr = req['printing_time'].split()[:-2]
    # Общая продолжительность работы TODO брать из подзадачи уже просуммированное?
    dur = 0
    for p in pr:
        if p == 'Всего:':
            break
        ml, t = p.split('*')
        h, m = t.split('ч')
        ml, h, m = (int(i) for i in (ml, h, m[:-1]))
        dur += h * ml * 60 + m * ml
    log.debug('Summary time is %d m', dur)
    # Извлечение из аналитики даты и времени начала (s_ = start)
    s_h, s_m = (int(i) for i in an['Планируемое время работы'][:5].split(':'))
    s_day, s_mon, s_ye = (int(i) for i in an['Дата'].split('-'))
    # Перевод времени в минуты и даты в часы
    beg = s_h * 60 + s_m
    days = s_day + sum(months[0:s_mon - 1])

    # Во время Нового года перерывы убирались для 52 машины, но это было временное решение
    # if req["machine"] == "PM-52":
    #     breaks = (1440, 0)
    # else:
    #   breaks = (570, 630), (720, 780), (1290, 1350), (1440, 60)

    # 9:30-10:30   12:00-13:00   21:30-22:30  24:00-1:00 (переход на следующий день)
    # TODO сделать контроль перерывов из справочников
    breaks = (510, 570), (720, 780), (1230, 1290), (1440, 60)
    # Разбиение времени на отрезки
    periods = translator(plan_forward(days, beg, dur, breaks), s_ye)
    # Аналитики, которые добавятся в задачу
    ans = []
    # Одна аналитика для каждого кусочка времени
    for p in periods:
        log.info('Date: %s begin: %s end: %s', p[0], p[1], p[2])
        # Разные в зависимости от машин аналитики (хотя вообще они отличаюстся лишь названием)
        if req['machine'] == 'PM-52':
            ans.append({'id': 1862, 'items':  # Такой вот формат
                ((12066, p[0]), (12068, '<begin>{0}</begin><end>{1}</end>'.format(p[1], p[2])))})
        else:
            ans.append({'id': 1868, 'items':
                ((12092, p[0]), (12094, '<begin>{0}</begin><end>{1}</end>'.format(p[1], p[2])))})

    # Добавление действия со всеми аналитиками
    log.debug('Adding analytics...')
    action_add(req['id'], ans=ans)

    # Обработка аналитики для машины Polar

    # Работа на Polar занимает пол часа и должна стоять сразу перед работой на PM
    finish = an['Планируемое время работы'][:5]
    h = int(finish[:2])
    m = int(finish[-2:]) - 30
    # Если получился переход на час назад
    if m < 0:
        # TODO Переход на день назад? На месяц?
        h -= 1
        m += 60
    # Время начала работы на Polar - на пол часа раньше
    start = str(h) + ":" + str(m)
    log.info('For Polar, start time: %s, final time: %s', start, finish)
    # Добавление аналитики ОТДЕЛЬНЫМ от печатных машин действием
    log.debug('Adding Polar analytics...')
    action_add(req["id"], ans={'id': 1866, 'items':
        ((12086, an['Дата']), (12088, '<begin>{0}</begin><end>{1}</end>'.format(start, finish)))})


# В отличие от бумаги, аналитика по пластинам добавляется в задачу заказа
def materials_workout(an):
    if not an['Количество']:
        log.info('Amount not stated, skipping')
        notify('Не указано количество материала в аналитике!')
        return
    if an['Материал'] is None:
        log.info('Material not stated, skipping')
        notify('Не указан материал!')
        return
    # Получаем индекс задачи с материалами
    task_id = find_record(an['Материал'], 1382)
    task = task_get(task_id)
    # И получаем остаток
    lft = get_custom_field(task, "Остаток")
    leftover_id = lft.field.id.string
    leftover_s = lft.value.string
    author_id = get_custom_field(task, 'Автор действия').field.id.string
    # Если кто-то стёр остаток (тупая проверка)
    if not leftover_s:
        leftover = 0
    else:
        leftover = int(leftover_s)
    log.info("Old value is %d", leftover)
    # Расчёт остатка
    final = leftover + int(find_record(an["Баланс"], 1378, 5044)) * int(an['Количество'])
    log.info("New value is %d", final)
    # Защита от дурака
    if final < 0:
        log.warning("Final amount is below zero, skipping")
        notify("Количество пластин не может быть отрицательным!")
        return
    # Заполнение остатка и автора действия
    task_update(task_id, (leftover_id, final), (author_id, req['author']))
    # Дозаполнение аналитики - заполнение остатка, задачи (для дальнейшего сбора аналитики) TODO и машины?
    act = req["action_link"][-7:]
    an_key = get_analytics_key(act)
    action_update(act, ans={"id": 1860, "items": [(12362, final), (12360, leftover_s)], "key": an_key})


print('Content-type: text/plain;charset=utf-8\n')
log.info('========== TASK ANALYTICS REQUEST')

get_request(cgi.FieldStorage())

try:
    # Разбор аналитики в словарь
    analy = parse_analytics(req["analytics"])
    # Есть два вида аналитики - на пластины и на пересчёт времени работы
    if analy['name'] == 'Планируемое время работы (без машины)':
        log.info('@@@@@@@@ PM PLANS')
        plans_workout(analy)
    elif analy['name'] == 'Материалы для печати':
        log.info('@@@@@@@@ MATERIALS WORKOUT')
        materials_workout(analy)
    else:
        log.warning("Unknown analytics")
except ConnectionError:
    pass
except Exception:
    log.critical("Something went wrong!", exc_info=True)

remove_blocker(req["id"])
