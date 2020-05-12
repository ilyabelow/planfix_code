#!/usr/bin/python3
# -*- coding:utf-8 -*-

from interface import *


#
# Управление резервациями бумаги
#

# Удаление записи
def delete_paper(r):
    log.info('Reservation of paper %s will be deleted', r)
    # Определение номера слота в задаче удаляемой бумаги, в котором содержится задача
    slot = find_slot(r, req['id'])
    log.debug('Slot: %d', slot)
    # Удаляется не бумага или кто-то уже стёр резервацию
    if slot is None or slot == -1:
        return
    # Удаление резервации
    log.debug('Deleting reservation...')
    # slot * 2 - потому что индексы полей почему-то различаются на 2
    task_update(r, (890 + slot * 2, ""), (854 + slot * 2, ""))
    log.info('Reservation is deleted')


# Добавление записи
def add_paper(r, amount):
    log.info('Reserving %s pieces of paper %s', amount, r)
    # Поиск пустого слота. При просмотре XML если поле с задачей пусто, то оно равно 0 а не пустой строке
    slot = find_slot(r, '0')
    log.debug('Slot: %d', slot)
    # Показатель того, что в слоте резервации была не бумага (нотификация в find_slot)
    if slot is None:
        return
    # У бумаги не оказалось пустого слота
    if slot == -1:
        log.warning('No empty reservation slot in paper %s', r)
        # Телеграм уже пнул!
        notify('У одной из бумаг нет свободных слотов для резервирования и она не добавилась.'
               ' Удалите ненужные резервации и попробуйте снова')
        return
    log.debug('Placing reservation...')
    # Уножить на два - потому что индексы полей идут через один
    task_update(r, (890 + slot * 2, req['id']), (854 + slot * 2, amount))
    log.info('Reservation placed...')


# Функция, просматривающая слоты резервации в бумаге и находящая, есть ли искомый заказ
def find_slot(paper_id, entry):
    log.debug('Getting task %s to find %s in its reservations...', paper_id, entry)
    # Суп бумаги
    paper = task_get(paper_id)
    if paper.template.string != '1276446':  # Проверка, является ли задача бумагой. 1276446 - id шаблона бумаги
        log.warning('Task in reservation is not a paper task')
        # Чисто человеческая ошибка
        notify('Задача в резервации не является бумагой')
        return

    # Получение списка слотов резерваций
    slots = get_custom_field(paper, 'Резерв #1', 'Резерв #2', 'Резерв #3')
    for x in range(3):  # Поиск в слотах названия заказа
        if slots[x].value.string == entry:
            log.info('Entry found on position', x)
            return x
    log.info('Entry not found')
    # -1 - показатель того, что запись не найдена
    return -1


#
# Массовое изменение резерваций
#


# Внесение резерваций при создании задачи
def create():
    log.info('The task %s have been created, making reservations', req['name'])
    # Добавление трёх слотов поочерёдно
    for r in '1', '2', '3':
        log.debug('Slot #' + r)
        # Если в поле ничего нет, то оно не отправляется вовсе
        if 'id' + r not in req:
            continue
        # Та же фигня. TODO Разрешить количество 0?
        if 'am' + r not in req:
            log.warning('Amount for slot %s not stated', r)
            notify('Не указано количество бумаги для резервирования в слоте', r, '!')
            continue
        # Добавление резервации
        add_paper(req['id' + r], req['am' + r])


# Удаление всех оставшихся резерваций при завершении задачи
def complete():
    log.info('The task %s have been deleted/completed, deleting reservations', req['name'])
    for r in '1', '2', '3':
        log.debug('Slot #' + r)
        # Если в слоте пусто
        if 'id' + r not in req:
            continue
        # Удаляем невзирая на количество
        delete_paper(req['id' + r])


#
# Единичное изменение резервации
#


# Добавление одной резервации
def add():
    # Если слот пустой
    if 'paper_id' not in req:
        log.warning('Paper not stated')
        notify('В слоте', str(int(req['slot']) + 1), 'не указана бумага для резервирования')
        return
    # Если количество пусто
    if 'amount' not in req:
        log.warning('Amount not stated')
        notify('Не указано количество бумаги', req['paper_name'], 'из слота', str(int(req['slot']) + 1))
        return
    log.info('Adding reservation for %s', req['paper_id'])
    add_paper(req['paper_id'], req['amount'])


# Удаление одной резервации
def pop():
    # Кто-то уже вручную стёр
    if 'paper_id' not in req:
        log.warning('Paper not stated')
        return
    # Удаляем невзирая на количество
    log.info('Popping reservation of paper %s', req['id'])
    delete_paper(req['paper_id'])


print('Content-type: text/plain;charset=utf-8\n')
log.info('========== RESERVATION')

get_request(cgi.FieldStorage())

try:
    log.info(req['action'].upper())
    # Внесение резерваций при создании задачи
    if req['action'] == 'Create':
        create()
    # Удаление всех оставшихся резерваций при завершении задачи
    elif req['action'] == 'Complete':
        complete()
    # Добавление новой резервации
    elif req['action'] == 'Add':
        add()
    # Удаление резервации
    elif req['action'] == 'Pop':
        pop()
except ConnectionError:
    pass
except Exception:
    log.error('Something went wrong!', exc_info=True)
