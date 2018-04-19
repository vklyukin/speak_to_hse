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
                if lesson["stream"].contain(minor.upper()+"_МНР"):
                    answer.append({"date":lesson["date"],"time":lesson["beginLesson"]+' - '+lesson["endLesson"],"dayofweek":lesson["dayOfWeekString"],"building":lesson["building"],"discipline":lesson["discipline"], "kindofwork":lesson["kindOfWork"]})
        myfile.close()
        return answer
    except:
        return ["Что-то пошло не так"]

minors_list = {"би": "Бизнес-информатика","ск":"Современная культура: теории и практика","псб":"Правовая среда бизнеса","мен":"Менеджмент","нт":"Нейросетевые технологии ",
               "псх":"Психология","флс":"Философия","иад":"Интеллектуальный анализ данных","юр":"Юриспруденция","бпд":"Безопасность предпринимательской деятельности",
               "ммк":"Медиа и массовые коммуникации","пэ":"Прикладная экономика","мо":"Международные отношения","урб":"Урбанистика","сп":"Современная политика",
               "со":"В лабиринтах культуры: социологический путеводитель по современным обществам","ил":"История литературы: от классики до постмодерна","мс":"Математические структуры",
               "физ":"Мир глазами физиков: от черных дыр к кубитам","вост":"Востоковедение","эфком":"Инструменты эффективной коммуникации: рассказ как жанр, наука и искусство",
               "истпр":"История правовой и политической мысли","истфил":"История философии","мим":"Междисциплинарные исследования медиа","мэ":"Мировая экономика","навыки":"""Навыки XXI века: 4 "К" """,
               "прч":"Права человека ","пса":"Прикладной статистический анализ","ист":"Прошлое в настоящем: люди, города, страны","публп":"Публичная политика",
               "стартап":"Стартап: дизайн нового бизнеса ","техпр":"Технологическое предпринимательство"}
