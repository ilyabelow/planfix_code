from interface import *


# def get_analytics_key(link):
#     print("Getting action...", end="")
#     t_res = action_get(link)
#     if not t_res: return
#     key = t_res.response.action.analitics.analitic.key.string
#     print("Analytics key is", key)
#     return key


def parse_analytics(s):
    an = list()
    spl_s = s[3:-5].split(sep="<br/><b>")
    for st in spl_s:
        d = dict()
        d["name"] = st[:st.find("</b>")]
        st = st[st.find("</b>") + 9:]
        while len(st) > 0:
            br = st.find("<br/>")
            div = st.find(" : ")
            if not st[div + 3:br]:
                d[st[:div]] = None
            else:
                d[st[:div]] = st[div + 3:br]
            st = st[br + 5:]
        an.append(d)
    return an


def request_action_updatea(action_id, deleted_key, an_id, *args):
    action_update = '<?xml version="1.0" encoding="UTF-8"?><request method="action.update"><account>{0}</account><action>' \
                    '<analitics><analitic><analiticData>'.format(account)
    for a in args:
        action_update = action_update + '<itemData><fieldId>{0}</fieldId><value>{1}</value></itemData>'.format(a[0],
                                                                                                               a[1])

    action_update = action_update + '</analiticData><id>{1}</id></analitic></analitics><deletedAnalitics><key>{2}</key>' \
                                    '</deletedAnalitics><id>{3}</id></action>' \
                                    '<sid>{0}</sid>'.format("{0}", an_id, deleted_key, action_id)
    return make_request(action_update)


# act = '6868636'
# k = get_analytics_key(act)
# an = parse_analytics("<b>Планируемое время работы на PM-74</b><br/>Дата : 18-03-2017<br/>Планируемое время работы : 19:00 - 19:30<br/>Сотрудник : Илья Белов<br/><br/>")[0]

# request_action_update(act, None, {"id":1868, "items":((12094,"<begin>1:0</begin><end>2:0</end>"),(12092,"10-03-2017")), "key":k})        # 74
# request_action_update(act, None, {"id":1862, "items":((12068,"<begin>00:00</begin><end>01:00</end>"),(12066,"10-03-2017")), "key":k})        # 52

if 0:
    make_request('<?xml version="1.0" encoding="UTF-8"?><request method="action.update">'
                 '<account>seven</account><action><analitics><analitic><analiticData>'
                 '<itemData><fieldId>12090</fieldId><value>137328</value></itemData>'
                 '<itemData><fieldId>12086</fieldId><value>29-03-2017</value></itemData>'
                 '<itemData><fieldId>12088</fieldId><value><begin>12:05</begin><end>12:05</end></value></itemData>'
                 '</analiticData><id>1866</id></analitic></analitics><id>6865774</id></action><sid>{0}</sid>')

# request_action_updatea(act, k, 1836, (11978, 137328),(11940, "20-03-2017"), (11942, "<begin>" + an["Планируемое время работы"][:5] +"</begin><end>" + an["Планируемое время работы"][8:] + "</end>"))
# print(request_analytics_get(k).prettify())

# ТЕСТ АНАЛИТИК
# print(make_request('<?xml version="1.0" encoding="UTF-8"?><request method="analitic.getOptions"><account>7-print</account><analitic><id>1870</id></analitic><sid>{0}</sid>').prettify())
# print(request_analytics_get(k).prettify())
'''<?xml version="1.0" encoding="UTF-8"?>
<response status="ok">
 <analitic>
  <id>
   1862
  </id>
  <name>
   Планируемое время работы на PM-52
  </name>
  <group>
   <id>
    1
   </id>
  </group>
  <fields>
   <field>
    <id>
     12066
    </id>
    <num>
     0
    </num>
    <name>
     Дата
    </name>
    <type>
     DATE
    </type>
   </field>
   <field>
    <id>
     12068
    </id>
    <num>
     1
    </num>
    <name>
     Планируемое время работы
    </name>
    <type>
     TIMEPERIOD
    </type>
   </field>
  </fields>
 </analitic>
</response>



<?xml version="1.0" encoding="UTF-8"?>
<response status="ok">
 <analitic>
  <id>
   1868
  </id>
  <name>
   Планируемое время работы на PM-74 NEW
  </name>
  <group>
   <id>
    1
   </id>
  </group>
  <fields>
   <field>
    <id>
     12092
    </id>
    <num>
     0
    </num>
    <name>
     Дата
    </name>
    <type>
     DATE
    </type>
   </field>
   <field>
    <id>
     12094
    </id>
    <num>
     1
    </num>
    <name>
     Планируемое время работы
    </name>
    <type>
     TIMEPERIOD
    </type>
   </field>
  </fields>
 </analitic>
</response>'''


def request_action_adda(t_id, comment, user, analy):
    action_add = '<?xml version="1.0" encoding="UTF-8"?><request method="action.add"><account>{0}</account>' \
                 '<action>'.format(account)
    if analy:
        action_add += "<analitics>"
        action_add += "<analitic><analiticData>"
        for it in analy["items"]:
            action_add += '<itemData><fieldId>{0}</fieldId><value>{1}</value></itemData>'.format(it[0], it[1])
        action_add += "</analiticData><id>{0}</id></analitic>".format(analy["id"])
        action_add += '</analitics>'
    if comment:
        action_add += '<description>{0}</description>'.format(comment)
    if user:
        action_add += '<notifiedList><user><id>{0}</id></user></notifiedList>'.format(user)
    action_add += '<task><id>{1}</id></task></action><sid>{0}</sid>'.format("{0}", t_id)

    return make_request(action_add)


# request_action_add(1295984, "бу", 137328, {"id":1866, "items":((12090,137328),(12086,"29-03-2017"),(12088,"<begin>12:00</begin><end>13:00</end>"))})


'''


log("Getting task to access print time...", end=" ")
q = request_task_get(27081)
print_time = get_custom_field(q, "Время печати").value.string
log("Print time is", print_time)
pr = print_time.split()
time = "12:00"
sum_h, sum_m = (int(i) for i in time.split(":"))
log(sum_h, sum_m)
for p in pr:
    ml, t = p.split("*")
    h, m = t.split("ч")
    ml, h, m = (int(i) for i in (ml, h, m[:-1]))
    sum_h += h * ml
    sum_m += m * ml

    log(ml,h,m)
sum_h += sum_m // 60
sum_m %= 60
log(sum_h, sum_m)

an = dict()
an["Бумага."] = "..."

task = None
for i in 1, 2, 3:
    log("Getting list of paper on page",i,"...", end=" ")
    ls = request_task_list(114838, i)
    if ls.response.task.title.string == an["Бумага."]:
        task = ls.response.task
    else:
        for sib in ls.response.task.next_siblings:
            if sib.title.string == an["Бумага."]:
                task = sib
                break
    if task:
        log("Paper was found")
    else:
        log("Paper wasn't found")

task_id = task.id.string
log("Paper's id is", task_id)
leftover = int(get_custom_field(task, "Остаток").value.string)
log("Paper's leftover is", leftover)

'''

# request_action_update(6869750, ":(", None, None, 1)

# requests.post("https://api.telegram.org/bot303817894:AAHQvjuKCQmzljubZy2O_4m_EZdAuhLNmOk/sendMessage?chat_id=231375784&text=Test!")

# request_action_add(1296542, "fgaf", None, None)

months = 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31


def translator(periods):
    per = []
    for p in periods:
        begin = str(p[1] // 60) + ":" + str(p[1] % 60)
        end = str(p[2] // 60) + ":" + str(p[2] % 60)
        days = p[0]
        mon = 1
        for i in range(12):
            if days <= months[i]:
                mon = i + 1
                break
            days -= months[i]
        per.append(["2017-{0}-{1}".format(mon, days), begin, end])
    return per


#
# req = {"id":1294080, "author": 137328}
# an = {"Баланс":"Расход","Количество":123, "Дата":"02-04-2017 15:10","Заказ":"", "Примечание": "Флоп"}

# request_action_add(req["id"], ans={"id":1870, "items": (
#    (12096, req["id"]),
#    (12098, an["Баланс"]),
#    (12100, an["Количество"]),
#    (12102, an["Дата"]),
#    (12104, an["Заказ"]),
#    (12106, req["author"]),
#    (12108, an["Примечание"]))})

# print(analytics_get(get_analytics_key(6877430)).prettify())

# print(request_task_get(number=25363).prettify())

# request_action_update(6894720, ans= {"id":1870, "items":{(12120,12345)}, "key":get_analytics_key(6894720)})

# request_action_update(7059728, ans={"id": 1870, "items": [(12100, 123)], "key": get_analytics_key(7059728)})

# print(action_update(7123586, "Тест отправки сообщения нескольким пользователям", user=137328))
# 126596
# 137328
# 1318102
# req['id'] = 1294080
# log.error("hi")\
# log.error("А у вас ошибка!")
# Разбивает промежуток времени на кусочки в зависимости от введённых перерывов
# Перерыв - пара время начала [0] и время конца [1] перерыва в минутах (всё в минутах)
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
                print(diff)
                if diff >= dur:
                    end = begin + dur
                    dur = 0
                else:
                    end = b[0]
                    dur -= diff
            periods.append([date, begin, end])
            begin = b[1]
            if b[1] < b[0]:
                date += 1
            if dur == 0:
                break
    return periods


ac = 7385446


# log.warning('hello')
# action_add(1294080, 'Ping', user=137328)
# print(make_request('<?xml version="1.0" encoding="UTF-8"?><request method="analitic.getData"><account>7-print</account><analiticKeys><key>52992</key></analiticKeys><sid>{0}</sid>').prettify())
print(make_request('<?xml version="1.0" encoding="UTF-8"?><request method="analitic.getOptions"><account>7-print</account><analitic><id>1860</id></analitic><sid>{0}</sid>').prettify())
# action_update(7386104, hide=True)
# print(get_structure(10,71).prettify())
# print(get_record(10,71).prettify())
# print(get_handbook_field(get_record(10,70), 4970).value.string)
# print(task_update(1375068, duration=100, name='Название из скрипта, ы'))

