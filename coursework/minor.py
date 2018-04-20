import json
import urllib.request
import urllib.error
from datetime import *
import global_constants as gc

def get_timetable():
    today = datetime.today().date()
    today_plus_week = datetime.today().date()+timedelta(days=7)
    url = "http://ruz.hse.ru/ruzservice.svc/lessons?fromdate={0}&todate={1}".format(today.strftime("%Y.%m.%d"), today_plus_week.strftime("%Y.%m.%d"))
    try:
        response = urllib.request.urlopen(url).read()
    except urllib.error.HTTPError:
        answer = 'Неверный запрос.'
    except urllib.error.URLError:
        answer = 'Сервер недоступен в данный момент'
    else:
        output = response.decode('utf-8')
        jsonstring = json.loads(output)
        outJson = []
        for item in jsonstring:
            if item['disciplinetypeload'] == 3:
                outJson.append(item)
        with open(gc.timetable_name, "w") as myfile:
            json.dump(outJson, myfile)
        myfile.close()

def get_info_minor(minor: str) -> list:
    try:
        answer = []
        with open(gc.timetable_name, "r") as myfile:
            timetable = json.load(myfile)
            for lesson in timetable:
                if lesson["stream"].find(minor) != -1 and lesson["stream"].find("_МНР") != -1:
                    answer.append({"date":lesson["date"],"time":lesson["beginLesson"]+' - '+lesson["endLesson"],"dayofweek":lesson["dayOfWeekString"],"building":lesson["building"],"discipline":lesson["discipline"], "kindofwork":lesson["kindOfWork"], "auditorium":lesson["auditorium"], "lecturer":lesson["lecturer"]})
        myfile.close()
        return answer
    except:
        return ["Что-то пошло не так"]

minors_list = {"БИ": "Бизнес-информатика","СК":"Современная культура: теории и практика","ПСБ":"Правовая среда бизнеса","Мен":"Менеджмент","НТ":"Нейросетевые технологии ",
               "Псх":"Психология","Флс":"Философия","ИАД":"Интеллектуальный анализ данных","Юр":"Юриспруденция","БПД":"Безопасность предпринимательской деятельности",
               "ММК":"Медиа и массовые коммуникации","ПЭ":"Прикладная экономика","МО":"Международные отношения","Урб":"Урбанистика","СП":"Современная политика",
               "СО":"В лабиринтах культуры: социологический путеводитель по современным обществам","ИЛ":"История литературы: от классики до постмодерна","МС":"Математические структуры",
               "Физ":"Мир глазами физиков: от черных дыр к кубитам","Вост":"Востоковедение","ЭфКом":"Инструменты эффективной коммуникации: рассказ как жанр, наука и искусство",
               "ИстПр":"История правовой и политической мысли","Истфил":"История философии","МИМ":"Междисциплинарные исследования медиа","МЭ":"Мировая экономика","Навыки":"""Навыки XXI века: 4 "К" """,
               "ПрЧ":"Права человека ","ПСА":"Прикладной статистический анализ","Ист":"Прошлое в настоящем: люди, города, страны","ПублП":"Публичная политика",
               "Стартап":"Стартап: дизайн нового бизнеса ","ТехПр":"Технологическое предпринимательство"}
