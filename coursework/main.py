import telebot
import global_constants
import re
import pickle
from telebot import types
from speechkit1_0 import speech_to_text
from speechkit1_0 import SpeechException
from neural_by_requests import tokenize_words
from nn_learning import *
from common import get_info_common
#creating bot object
bot = telebot.TeleBot(global_constants.token)
#modifying keyboard
markup = types.ReplyKeyboardMarkup()
markup.row('/help')
#loading of trained model
decision_filename = 'naive_classify.pkl'
decision_model_pkl = open(decision_filename, 'rb')
decision_model = pickle.load(decision_model_pkl)
#file, which containing dict with emails of users
email_filename = 'users_email.pkl'
with open(email_filename, 'rb') as file:
    users_email = pickle.load(file)
file.close()
#steps of logging of user
user_steps = {}
USER_LOGGING = -1
USER_ACCEPTED = 1

@bot.message_handler(commands=['start'])
def start_conversation(message):
    bot.send_message(message.chat.id,global_constants.message_command_start ,reply_markup=markup)
    if users_email.get(message.chat.id) != None:
        bot.send_message(message.chat.id, global_constants.message_command_start_login.format(users_email[message.chat.id]))
    else:
        bot.send_message(message.chat.id,  global_constants.message_command_start_first)
        user_steps.update({message.chat.id: USER_LOGGING})

@bot.message_handler(commands=['email'])
def login_by_email(message):
    user_steps.update({message.chat.id: USER_LOGGING})
    bot.send_message(message.chat.id, global_constants.message_command_start_first)

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


@bot.message_handler(commands=['help'])
def start_conversation(message):
    bot.send_message(message.chat.id, 'Попроси у меня показать расписание путем отправки голосового сообщения',reply_markup=markup)

@bot.message_handler(content_types=['text'])
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
        type = decision_model.classify(RequestItem(text.split(),'').features(all_words))
        bot.send_message(message.chat.id, type)
        if type == 'common\n':
            bot.send_message(message.chat.id, get_info_common(text, users_email[message.chat.id]))
        else:
            print('blabla')
        tokens = tokenize_words(text)


if __name__ == '__main__':
    bot.polling(none_stop=True)