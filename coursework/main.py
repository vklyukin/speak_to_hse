import telebot
import global_constants
from telebot import types
from speechkit1_0 import speech_to_text
from speechkit1_0 import SpeechException

bot = telebot.TeleBot(global_constants.token)

markup = types.ReplyKeyboardMarkup()
markup.row('/help')

@bot.message_handler(commands=['start'])
def start_conversation(message):
    bot.send_message(message.chat.id,global_constants.message_command_start ,reply_markup=markup)

@bot.message_handler(commands=['help'])
def start_conversation(message):
    bot.send_message(message.chat.id, 'Попроси у меня показать расписание путем отправки голосового сообщения',reply_markup=markup)

@bot.message_handler(content_types=['text'])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, 'К сожалению, я понимаю только речь, так что попроси у меня показать расписание голосом')

@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    try:
        # обращение к нашему новому модулю
        text = speech_to_text(message, file_info.file_path)
    except SpeechException:
        # Обработка случая, когда распознавание не удалось
        bot.send_message(message.chat.id, 'К сожалению, я не смог разобрать твою речь')
    else:
        # Перевод слов текста в список векторов w2v
        bot.send_message(message.chat.id, text)
if __name__ == '__main__':
    bot.polling(none_stop=True)