from bs4 import BeautifulSoup
from hashlib import md5
from requests import post, get
from yaml import safe_load
import logging.config
# Необходимо для других скриптов
from time import strftime
import cgi
from time import sleep


# Отправка запроса + переавторизация, обработка ошибок, конвертирование ответа в читаемый формат
def make_request(data, tries=0):
    if tries > 2:
        log.critical('Too many tries', exc_info=True)
        raise ConnectionError
    # Отправка запроса
    request = add_signature(data.format(sid))
    log.debug('Sending request...')
    response = post("https://api.planfix.ru/xml/", data=request.encode(), auth=(api_token, None))
    # Извлечение ответа
    resp_str = response.content.decode()
    response.close()
    log.debug('Done, response')
    log.debug(resp_str)
    soup = BeautifulSoup(resp_str, "html.parser")
    # TODO Сделать обработку ошибок
    if soup.response["status"] == "error":
        if soup.response.code.string == "0005":  # 0005 = сессия истекла, переавторизация
            authorise()
            # Переотправка запроса рекурсией
            soup = make_request(data)
        elif soup.response.code.string == "4002":  # 4002 = действия не существует (обычно брехня)
            log.warning('Action doesn\'t exist, retry')
            soup = make_request(data, tries + 1)
        else:  # Пока что при любых других ошибках выполненеи программы сразу же прекращается
            log.critical(
                "An error occured while making request, code:" + soup.response.code.string, exc_info=True)
            raise ConnectionError
    return soup


# Авторизирование
def authorise():
    log.debug("Authorising...")
    # Добавление подписи к форме для авторизирования
    auth = add_signature('<?xml version="1.0" encoding="UTF-8"?><request method="auth.login"><account>{0}</account>'
                         '<login>{1}</login><password>{2}</password>'.format(account, login, password))
    # Отправка запроса
    auth_response = post("https://api.planfix.ru/xml/", data=auth, auth=(api_token, None))
    soup = BeautifulSoup(auth_response.content, "html.parser")
    auth_response.close()
    # Если произошла ошибка, то выходим из программы. Тут не можут быть таких ошибок, которые можно было бы обработать
    if soup.response["status"] == "error":
        log.error("An error occured while authorising")
        log.error("Request:")
        log.error(auth)
        log.error("Error code: %s Message: %s", soup.response.code.string, soup.response.message.string)
        raise ConnectionError
    # Извлечение и сохранение нового ключа
    global sid, f
    sid = soup.response.sid.string
    log.debug('sid = %s', sid)
    f = open("sid.txt", "w")
    f.write(sid)
    f.close()


# Составление и дабовление цифровой подписи
def add_signature(string):
    soup = BeautifulSoup(string, "html.parser")
    # Подпись состоит из названия функции, значений всех полей и ключа.
    # Значения полей должны быть в алфавитном порядке, но я не знаю, как это
    # сделать, поэтому я сортирую поля вручную :(
    signature = soup.request["method"] + "".join(soup.get_text().split(sep="\n")) + sig_key
    signature = md5(signature.encode('utf-8')).hexdigest()
    return string + "<signature>" + signature + "</signature></request>"


# Запрос получения данных задачи
def task_get(task_id='', number=''):  # Может использоваться либо number либо id
    return make_request('<?xml version="1.0" encoding="UTF-8"?><request method="task.get"><account>{1}</account>'
                        '<sid>{0}</sid><task><id>{2}</id><general>{3}</general></task>'
                        .format('{0}', account, task_id, number))


# Запрос на обновление данных задачи
def task_update(task_id, *args, duration=None, name=None):  # args - пары id поля - значение поля
    request = '<?xml version="1.0" encoding="UTF-8"?><request method="task.update">' \
              '<account>{1}</account><sid>{0}</sid><task>'.format('{0}', account)
    if len(args) > 0:
        request = request + '<customData>'
        for a in args:
            request = request + '<customValue><id>{0}</id><value>{1}</value></customValue>'.format(a[0], a[1])
        request = request + '</customData>'
    if duration is not None:
        request = request + '<duration>{0}</duration><durationUnit>0</durationUnit>'.format(duration)
    request = request + '<id>{0}</id>'.format(task_id)
    if name is not None:
        request += '<title>{0}</title>'.format(name)
    request += '</task>'
    return make_request(request)


# Запрос на получение данных действия
def action_get(action_id):
    return make_request('<?xml version="1.0" encoding="UTF-8"?><request method="action.get"><account>{1}</account>'
                        '<action><id>{2}</id></action><sid>{0}</sid>'.format("{0}", account, action_id))


# Добавление действия
def action_add(task_id, text=None, user=None, ans=None):
    request = '<?xml version="1.0" encoding="UTF-8"?><request method="action.add"><account>{0}</account>' \
              '<action>'.format(account)
    # Добавление аналитик если есть
    if ans:
        request += "<analitics>"
        # Если отправлена одна аналитика (словарь), а не список аналитик, то такой список создаётся (из одного элемента)
        if not isinstance(ans, list):
            ans = [ans]
        # Обработка каждой аналитики
        for analy in ans:
            request += "<analitic><analiticData>"
            # Добавление полей аналитики
            for it in analy["items"]:
                request += '<itemData><fieldId>{0}</fieldId><value>{1}</value></itemData>'.format(it[0], it[1])
            request += "</analiticData><id>{0}</id></analitic>".format(analy["id"])
        request += '</analitics>'
    # Добавление текста если есть
    if text:
        request += '<description>{0}</description>'.format(text)
    # Уведомление человекам если есть кому
    if user:
        # Та же штука как и с аналитиками
        if not isinstance(user, list):
            user = [user]
        request += '<notifiedList><user>'
        for u in user:
            request += '<id>{0}</id>'.format(u)
        request += '</user></notifiedList>'
    request += '<task><id>{1}</id></task></action><sid>{0}</sid>'.format("{0}", task_id)
    return make_request(request)


# Обновление действия. Работает почти так же, как и предыдущая функция
def action_update(action_id, text=None, user=None, ans=None, deleted_key=None, hide=False):
    request = '<?xml version="1.0" encoding="UTF-8"?><request method="action.update"><account>{0}</account>' \
              '<action>'.format(account)
    # Добавление аналитик если есть
    if ans:
        request += "<analitics>"
        # Если отправлена одна аналитика (словарь), а не список аналитик, то такой список создаётся (из одного элемента)
        if not isinstance(ans, list):
            ans = [ans]
        # Обработка каждой аналитики
        for analy in ans:
            request += "<analitic><analiticData>"
            # Добавление полей аналитики
            for it in analy["items"]:
                request += '<itemData><fieldId>{0}</fieldId><value>{1}</value></itemData>'.format(it[0], it[1])
            # УКАЗАНИЕ КЛЮЧА ИЗМЕНЯЕМОЙ АНАЛИТИКИ
            if "key" in analy:
                request += '<key>{0}</key>'.format(analy["key"])
            request += "</analiticData><id>{0}</id></analitic>".format(analy["id"])
        request += '</analitics>'
    # Запись ключа аналитики, которую надо удалить (если есть)
    if deleted_key is not None:
        request += "<deletedAnalitics><key>{0}</key></deletedAnalitics>".format(deleted_key)
    # Добавление текста если есть
    if text:
        request += '<description>{0}</description>'.format(text)
    # Собсна id самого действия
    request += '<id>{0}</id>'.format(action_id)
    # Спрятывание сообщения
    if hide:
        request += '<isHidden>1</isHidden>'
    # Уведомление человекам если есть кому TODO Эта функция не робит
    if user:
        # Та же штука как и с аналитиками
        if not isinstance(user, list):
            user = [user]
        request += '<notifiedList><user>'
        for u in user:
            request += '<id>{0}</id>'.format(u)
        request += '</user></notifiedList>'
    request += '</action><sid>{0}</sid>'.format("{0}")
    return make_request(request)


def get_structure(handbook, key):
    return make_request('''<?xml version="1.0" encoding="UTF-8"?>
    <request method="handbook.getStructure">
    <account>{1}</account>
    <handbook>
    <id>{2}</id>
    </handbook>
    <key>{3}</key>
    <sid>{0}</sid>'''.format('{0}', account, handbook, key))


def get_records(handbook, key=None):
    return make_request('<?xml version="1.0" encoding="UTF-8"?>'
                        '<request method="handbook.getRecords">'
                        '<account>{1}</account>'
                        '<handbook>'
                        '<id>{2}</id>'
                        '</handbook>'
                        '<pageSize>100</pageSize>'
                        '{3}'
                        '<sid>{0}</sid>'.format('{0}', account, handbook, '<parentKey>{0}</parentKey>'.format(key)*(key != None)))


def get_record(handbook, key):
    return make_request('<?xml version="1.0" encoding="UTF-8"?>'
                        '<request method="handbook.getRecord">'
                        '<account>{1}</account>'
                        '<handbook>'
                        '<id>{2}</id>'
                        '</handbook>'
                        '<key>{3}</key>'
                        '<sid>{0}</sid>'.format('{0}', account, handbook, key))


def find_record(name, handbook, seek_id=None):
    groups = [i.string for i in get_records(handbook).response.records.find_all('key')]
    groups.append(None)
    found = None
    for gkey in groups:
        records = get_records(handbook, gkey)
        gr = records.find_all('text')
        for field in gr:
            if field.string == name:
                found = field
                break
        else:
            continue
        break
    if found is None:
        return None
    if seek_id is None:
        return found.find_parent().value.string
    # print(found.find_parent('customdata'))
    ids = found.find_parent('customdata').find_all('id')
    for id in ids:
        if id.string == str(seek_id):
            found = id
            break
    else:
        return None
    return found.find_parent('customvalue').value.string


# Неиспользуемые функции запросов

# Запрос на получение данных аналитики
def analytics_get(analytics_id):
    return make_request('<?xml version="1.0" encoding="UTF-8"?><request method="analitic.getData">'
                        '<account>{1}</account>'
                        '<analiticKeys><key>{2}</key></analiticKeys><sid>{0}</sid>'
                        .format('{0}', account, analytics_id))


# Запрос на получение списка сотрудников
def get_user_list(group_id):
    return make_request('<?xml version="1.0" encoding="UTF-8"?><request method="user.getList"><account>{1}</account>'
                        '<pageCurrent>1</pageCurrent><pageSize>100</pageSize><sid>{0}</sid><userGroup>'
                        '<id>{2}</id></userGroup>'.format("{0}", account, group_id))


# Запрос на получение списка задач
def task_list(project, page=1):
    return make_request('<?xml version="1.0" encoding="UTF-8"?><request method="task.getList"><account>{1}</account>'
                        '<pageCurrent>{3}</pageCurrent><pageSize>100</pageSize><project><id>{2}</id>'
                        '</project><sid>{0}</sid><target>all</target>'.format("{0}", account, project, page))


# Парсинг аналитики из формата, в котором отправляет её сценарий. НЕ поддерживает множество аналитик
# TODO Сделать человеческое читывание аналитике с помощью запроса и XML разбора, а не с помощью рытья в кривом нечте
def parse_analytics(s):
    # Выход функции
    an = dict()
    # Рабочая строка. Сначала обрезаем лишние концы
    st = s[3:-5]
    # Имя находится перед первым </b>
    an["name"] = st[:st.find("</b>")]
    # Обрезание имени и первых </b><br/>
    st = st[st.find("</b>") + 9:]
    while len(st) > 0:
        # Текущее обрабатываемое поле отделается от остальных <br/>
        br = st.find("<br/>")
        # Название поля и его значение разделяются  :
        div = st.find(" : ")
        if not st[div + 3:br]:  # У поля нет значения
            an[st[:div]] = None  # st[:div] - название поля
        else:
            an[st[:div]] = st[div + 3:br]  # st[div + 3:br] - его значение
        st = st[br + 5:]  # Обрезание </br>
    log.info('Analytics dict:')
    log.info(an)
    return an


# Получение ключа аналитики
def get_analytics_key(action_id):
    log.debug("Getting action %d for analytics key...", action_id)
    t_res = action_get(action_id)
    key = t_res.response.action.analitics.analitic.key.string
    log.debug("Analytics key is %d", key)
    return key


# Извлечение из задачи значений кастомных полей
def get_handbook_field(task_soup, *ids):  # names - имена полей
    ret = list()
    for id in ids:
        # Если первое поле является искомым, то ура, записываем его
        if task_soup.customdata.customvalue.field.find("id").string != str(id):
            # Иначе просматриваем все последующие поля
            for sib in task_soup.customdata.customvalue.next_siblings:
                if sib.field.find("id").string == str(id):
                    ret.append(sib)
                    break
            else:
                # Не было найдено такого поля
                ret.append(None)
        else:
            ret.append(task_soup.customdata.customvalue)
    # Если запрашивалось одно поле, то отправляется только оно само, а не список из одного значения
    if len(ids) == 1:
        return ret[0]
    else:
        return ret


# Извлечение из задачи значений кастомных полей
def get_custom_field(task_soup, *names):  # names - имена полей
    ret = list()
    for name in names:
        # Если первое поле является искомым, то ура, записываем его
        if task_soup.customdata.customvalue.field.find("name").string != name:
            # Иначе просматриваем все последующие поля
            for sib in task_soup.customdata.customvalue.next_siblings:
                if sib.field.find("name").string == name:
                    ret.append(sib)
                    break
            else:
                # Не было найдено такого поля
                ret.append(None)
        else:
            ret.append(task_soup.customdata.customvalue)
    # Если запрашивалось одно поле, то отправляется только оно само, а не список из одного значения
    if len(names) == 1:
        return ret[0]
    else:
        return ret


# Конвертация cgi.FieldStorage в словарь
def get_request(inp):
    log.info("Incoming request:")
    for k in inp.keys():
        req[k] = inp.getvalue(k).strip()
    # Вывод запроса в лог
    for k, v in req.items():
        log.info(">> %s = %s", k, v)
    # Переодически автор не указывается
    if "author" not in req:
        log.warning("Author not stated, so notifications will not work properly!")
        req["author"] = ""
        req["author_name"] = "UNKNOWN"


# Быстрая отправка сообщений пользователю в задачу
def notify(*text):
    action_add(req['id'], ' '.join(text), req['author'])


# Снятия блокировки бота
def remove_blocker(task_id):
    sleep(5)
    log.debug('Removing blocker...')
    task_update(task_id, (862, 0))  # TODO Переделать поле, блокирующее бота


# Создатель хендлера
def get_handler(level=logging.ERROR, formatter=None):
    ph = TelegramHandler(level=level)
    ph.setFormatter(formatter)
    return ph


# Хедлер, отсылающий сообщение в Телеграм
class TelegramHandler(logging.Handler):

    def emit(self, record):
        get("https://api.telegram.org/secret/"
            "secret".format(self.format(record)))


# Константы
sig_key = 'secret'
api_token = "secret"
account = "secret"
login = "secret"
password = "secret"

req = {} # Временное решение, нужно переделать в объект сессии

# Импорт конфигурации лога
f = open("logging.yaml")
logging.config.dictConfig(safe_load(f))
f.close()
log = logging.getLogger('root')
log.info(strftime('%X'))

# Считывание предыдущего сида. В большенстве случаев между запросами сид не успевает просрочиться
f = open('sid.txt')
sid = f.readline()
f.close()
