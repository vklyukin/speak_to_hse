import telebot
import gensim
import re
import logging
import schedule
import pickle
import time
from telebot import types
from datetime import datetime, timedelta
from pymorphy2 import MorphAnalyzer
from speechkit1_0 import speech_to_text, SpeechException
from dataset_preparing import classes, vector_of_line, RequestItem, all_words
from common import get_info_common
from minor import minors_list, get_info_minor, get_timetable
import global_constants as gc
from random_forest_fitting import target_names
#creating bot object
bot = telebot.TeleBot(gc.token)
#creating w2v model
get_vector = gensim.models.KeyedVectors.load_word2vec_format(r'''ruwikiruscorpora_upos_skipgram_300_2_2018.vec''')
#creating objects for getting features
morph = MorphAnalyzer()
decision_tree = pickle.load(open(gc.submodel_filename, "rb"))
#modifying keyboard
markup = types.ReplyKeyboardMarkup()
markup.row('/help')
#Outputs debug messages to console
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
#loading of trained model
decision_model_pkl = open(gc.model_filename, 'rb')
decision_model = pickle.load(decision_model_pkl)
#file, which containing dict with emails of users
email_filename = 'users_email.pkl'
with open(email_filename, 'rb') as file:
    users_email = pickle.load(file)
file.close()
#file, which containing dict with minors of users
minor_filename = 'users_minor.pkl'
with open(email_filename, 'rb') as file:
    users_minor = pickle.load(file)
file.close()
#steps of logging of user
user_steps = {}
user_steps_minor = {}
USER_LOGGING = -1
USER_ACCEPTED = 1

@bot.message_handler(commands=['start'])
def start_conversation(message):
    bot.send_message(message.chat.id,gc.message_command_start ,reply_markup=markup)
    if users_email.get(message.chat.id) != None:
        bot.send_message(message.chat.id, gc.message_command_start_login.format(users_email[message.chat.id]))
    else:
        bot.send_message(message.chat.id,  gc.message_command_start_first)
        user_steps.update({message.chat.id: USER_LOGGING})

@bot.message_handler(commands=['email'])
def login_by_email(message):
    user_steps.update({message.chat.id: USER_LOGGING})
    bot.send_message(message.chat.id, gc.message_command_start_first)

@bot.message_handler(commands=['minor'])
def login_by_email(message):
    user_steps_minor.update({message.chat.id: USER_LOGGING})
    bot.send_message(message.chat.id, gc.message_command_start_set_minor)
    bot.send_photo(message.chat.id, gc.minors_list_photo_id)

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == USER_LOGGING)
def user_login(message):
    if len(re.findall(r":?@edu\.hse\.ru|@hse\.ru", message.text)) > 0:
        users_email.update({message.chat.id: message.text.strip().lower()})
        with open(email_filename, 'wb') as file:
            pickle.dump(users_email, file)
        file.close()
        user_steps[message.chat.id] = USER_ACCEPTED
        bot.reply_to(message, "Ваша почта подтверждена")
    else:
        bot.reply_to(message, "Неверный формат. Убедитесь, что ваша почта зарегестрирована на edu.hse.ru или hse.ru")
        #дописать settings, проверить, дописать посылку get-запроса с почтой юзера

@bot.message_handler(func=lambda message: user_steps_minor.get(message.chat.id) == USER_LOGGING)
def user_set_minor(message):
    answer = message.text.strip().lower()
    if answer in minors_list.keys():
        users_minor.update({message.chat.id:message.text.strip().lower()})
        with open(minor_filename, 'wb') as file:
            pickle.dump(users_email, file)
        file.close()
        user_steps_minor[message.chat.id] = USER_ACCEPTED
        bot.reply_to(message, "Майнор подтвержден: "+minors_list[answer])
    else:
        bot.reply_to("Неверный формат ввода аббревиатура майнора. Сверьтесь со списком")

@bot.message_handler(commands=['help'])
def start_conversation(message):
    bot.send_message(message.chat.id, 'Попроси у меня показать расписание путем отправки голосового сообщения',reply_markup=markup)

@bot.message_handler(content_types=['text', 'video', 'audio', 'document', 'photo', 'sticker','video_note','location', 'contact'])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, 'К сожалению, я понимаю только речь, так что попроси у меня показать расписание голосом')

@bot.message_handler(func=lambda message: message.voice.mime_type == 'audio/ogg', content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    try:
        # обращение к нашему новому модулю
        text = speech_to_text(message, file_info.file_path)
    except SpeechException:
        # Обработка случая, когда распознавание не удалось
        print(message.chat.id)
        bot.send_message(message.chat.id, 'К сожалению, я не смог разобрать твою речь')
    else:
        # Обработка фразы с помощью нейронной сети
        bot.send_message(message.chat.id, text)
        type = predict(text)
        bot.send_message(message.chat.id, type)
        if type == 'common':
            bot.send_message(message.chat.id, get_info_common(text, users_email[message.chat.id]))
        elif type == 'help':
            start_conversation(message)
        elif type == 'minor':
            lessons = get_info_minor(users_minor[message.chat.id])
            if len(lessons) > 0:
                current = lessons[0]["date"]
                answer = "**"+datetime.strptime(lessons[0]["date"], "%Y.%m.%d").strftime("%d.%m.%Y")+"**, "+lessons[0]["dayOfWeekString"]+"\n__"+lessons[0]["building"]+"__\n\n"+lessons[0]["discipline"]+", "+lessons[0]["time"]+"\n"
                for i in range(1,len(lessons)):
                    if lessons[i]["date"] != lessons[i-1]["date"]:
                        answer += "\n**"+datetime.strptime(lessons[i]["date"], "%Y.%m.%d").strftime("%d.%m.%Y")+"**, "+lessons[i]["dayOfWeekString"]+"\n__"+lessons[i]["building"]+"__\n\n"
                    elif lessons[i]["building"] != lessons[i]["building"]:
                        answer += "\n__"+lessons[i]["building"]+"__\n\n"
                    answer += lessons[0]["discipline"]+", "+lessons[0]["time"]+"\n"
            else:
                today = datetime.today().date().strftime("%d.%m.%Y")
                today_plus_week = (datetime.today().date() + timedelta(days=7)).strftime("%d.%m.%Y")
                bot.send_message("В период с {0} по {1} занятий по данному майнору нет".format(today, today_plus_week))


def predict(text:str) -> str:
    words = text.split()
    tree_result = classes[decision_tree.classify(RequestItem(words,'').features(all_words))]
    vector = vector_of_line(text, get_vector)
    features = [tree_result, get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "майнер_NOUN"), get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "спам_NOUN"),
        get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "расписание_NOUN"),get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "помощь_NOUN")]
    return target_names(decision_model.predict([features])[0])

schedule.every().day.at("04:00").do(get_timetable)

while True:
    try:
        if __name__ == '__main__':
            bot.polling(none_stop=True)
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(e)
        time.sleep(15)