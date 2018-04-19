import re
import json
import urllib.request
import urllib.error
from datetime import *

class DateException(Exception):
    def __init__(self, message):
        self.message = message

#regex pattern
date_expr = r"(\d{1,2}) (я:?января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)"
date_expr_day =  r"\d{1,2}"
date_expr_month = r":?января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
key_words = ['завтра','послезавтра', 'сегодня']
months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

def date_entity(text):
    given_words = text.split()
    now_date = datetime.today()
    #looking for date in key_words
    for word in key_words:
        if word in given_words:
            if word == 'завтра':
                ans_date = datetime.strftime(now_date+timedelta(days=1), "%Y.%m.%d")
            elif word == 'послезавтра':
                ans_date = datetime.strftime(now_date+timedelta(days=2), "%Y.%m.%d")
            else:
                ans_date = datetime.strftime(now_date, "%Y.%m.%d")
            print(ans_date)
            return ans_date
    #looking for date with reqular expression
    request_date = re.findall(date_expr, text)
    if len(request_date) > 0:
        date_day = int(re.findall(date_expr_day,request_date[0][0])[0])
        date_month = re.findall(date_expr_month, request_date[0][1])[0]
        for i in range(len(months)):
            if date_month == months[i]:
                date_month = i+1
                break
        try:
            if (date(now_date.year, date_month, date_day) >= now_date.date()):
                return datetime.strftime(date(now_date.year, date_month, date_day), "%Y.%m.%d")
            else:
                return datetime.strftime(date(now_date.year+1, date_month, date_day), "%Y.%m.%d")
        except ValueError:
            raise DateException('Некорректное значение даты. Повторите запрос ещё раз.')
    else:
        raise DateException('В вашем сообщении не найдено запроса на дату. Повторите запрос ещё раз.')

def get_info_common(text, user_id):
    try:
        _date = date_entity(text)
    except DateException as e:
        return e.message
    else:
        url = "http://ruz.hse.ru/ruzservice.svc/personlessons?fromdate={0}&todate={0}&receivertype=0&email={1}".format(str(_date),user_id)
        try:
            response = urllib.request.urlopen(url).read()
        except urllib.error.HTTPError:
            answer = 'Неверный запрос. Проверьте настройки почты или произнесите дату чётче.'
        except urllib.error.URLError:
            answer = 'Сервер недоступен в данный момент'
        else:
            output = response.decode('utf-8')
            jsonstring = json.loads(output)
            answer = "**"+str(_date)+"**"+"\n__________________________\n"
            for item in jsonstring:
                answer = answer + item['discipline']+', **'+item['auditorium']+'каб.**'+'\n**'+item['beginLesson']+'-'+item['endLesson']+'**\n__________________________\n'
        return answer