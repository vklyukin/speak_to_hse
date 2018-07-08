import telebot, gensim, re, logging, pickle, time, global_constants as gc
from datetime import datetime, timedelta
from pymorphy2 import MorphAnalyzer
from speechkit1_0 import speech_to_text, SpeechException
from dataset_preparing import classes, vector_of_line, RequestItem, all_words
from common import get_info_common
from minor import minors_list, get_info_minor, get_timetable, get_structured_timetable
from random_forest_fitting import target_names

# creating bot object
bot = telebot.TeleBot(gc.token)
# creating w2v model
get_vector = gensim.models.KeyedVectors.load_word2vec_format(r'''araneum_upos_skipgram_300_2_2018.vec''')
# creating objects for getting features
morph = MorphAnalyzer()
maxent_model = pickle.load(open(gc.submodel_filename, "rb"))
# modifying keyboard
markup = telebot.types.ReplyKeyboardMarkup()
markup.row('/help', '/minor', '/email')
# Outputs debug messages to console
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
# downloading the timetable for the next week
get_timetable()
# loading of trained model
decision_model_pkl = open(gc.model_filename, 'rb')
decision_model = pickle.load(decision_model_pkl)
decision_model_pkl.close()
# file, which containing dict with emails of users
email_filename = 'users_email.pkl'
with open(email_filename, 'rb') as file:
    users_email = pickle.load(file)
file.close()
# file, which containing dict with minors of users
minor_filename = 'users_minor.pkl'
with open(minor_filename, 'rb') as file:
    users_minor = pickle.load(file)
file.close()
# steps of logging of user
user_steps = {}
user_steps_minor = {}
USER_LOGGING = -1
USER_ACCEPTED = 1


@bot.message_handler(commands=['start'])
def start_conversation(message):
    bot.send_message(message.chat.id, gc.message_command_start, reply_markup=markup, parse_mode="html")
    bot.send_photo(message.chat.id, gc.yandex_logo_id)
    if users_email.get(message.chat.id) != None:
        bot.send_message(message.chat.id, gc.message_command_start_login.format(users_email[message.chat.id]),reply_markup=markup)
    else:
        bot.send_message(message.chat.id, gc.message_command_start_first,reply_markup=markup)
        user_steps.update({message.chat.id: USER_LOGGING})


@bot.message_handler(commands=['email'])
def login_by_email(message):
    user_steps.update({message.chat.id: USER_LOGGING})
    bot.send_message(message.chat.id, gc.message_command_start_first, reply_markup=markup)


@bot.message_handler(commands=['minor'])
def login_by_minor(message):
    user_steps_minor.update({message.chat.id: USER_LOGGING})
    bot.send_message(message.chat.id, gc.message_command_start_set_minor, reply_markup=markup)
    bot.send_photo(message.chat.id, gc.minors_list_photo_id, reply_markup=markup)


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


@bot.message_handler(func=lambda message: user_steps_minor.get(message.chat.id) == USER_LOGGING)
def user_set_minor(message):
    answer = message.text.strip().lower()
    found = False
    for minor in minors_list.keys():
        if minor.lower() == answer:
            found = True
            users_minor.update({message.chat.id: minor})
    if not found:
        bot.reply_to(message, "Неверный формат ввода аббревиатура майнора. Сверьтесь со списком")
    else:
        with open(minor_filename, 'wb') as file:
            pickle.dump(users_minor, file)
        file.close()
        user_steps_minor[message.chat.id] = USER_ACCEPTED
        bot.reply_to(message, "Майнор подтвержден: " + minors_list[users_minor[message.chat.id]])


@bot.message_handler(commands=['help'])
def start_conversation(message):
    bot.send_message(message.chat.id, gc.answer_help, reply_markup=markup)


@bot.message_handler(
    content_types=['text', 'video', 'audio', 'document', 'photo', 'sticker', 'video_note', 'location', 'contact'])
def repeat_all_messages(message):
    bot.send_message(message.chat.id,
                     'К сожалению, я понимаю только речь, так что попроси у меня показать расписание голосом', reply_markup=markup)


@bot.message_handler(func=lambda message: message.voice.mime_type == 'audio/ogg', content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    try:
        # обращение к нашему новому модулю
        text = speech_to_text(message, file_info.file_path)
    except SpeechException:
        # Обработка случая, когда распознавание не удалось
        bot.send_message(message.chat.id, 'К сожалению, я не смог разобрать твою речь', reply_markup=markup)
    except MemoryError:
        bot.send_message(message.chat.id, 'Попробуйте записать сообщение покороче', reply_markup=markup)
    else:
        # Обработка фразы с помощью нейронной сети
        type = predict(text)
        if type == 'common':
            try:
                bot.send_message(message.chat.id, get_info_common(text, users_email[message.chat.id]),
                                 parse_mode='html', reply_markup=markup)
            except MemoryError:
                bot.send_message(message.chat.id, "Объем сообщения слишком велик", reply_markup=markup)
        elif type == 'spam':
            bot.send_message(message.chat.id, gc.answer_spam, parse_mode='html', reply_markup=markup)
        elif type == 'help':
            start_conversation(message)
        elif type == 'minor':
            try:
                lessons = get_info_minor(users_minor[message.chat.id])
                if len(lessons) > 0:
                    bot.send_message(message.chat.id, get_structured_timetable(lessons), parse_mode='html', reply_markup=markup)
                else:
                    today = datetime.today().date().strftime("%d.%m.%Y")
                    today_plus_week = (datetime.today().date() + timedelta(days=7)).strftime("%d.%m.%Y")
                    bot.send_message(message.chat.id,
                                     "В период с {0} по {1} занятий по данному майнору нет".format(today,
                                                                                                   today_plus_week), reply_markup=markup)
            except MemoryError:
                bot.send_message(message.chat.id, "Объем сообщения слишком велик", reply_markup=markup)
            except KeyError:
                bot.send_message(message.chat.id, "Сперва выберите интересующий майнор")


def predict(text: str) -> str:
    words = text.split()
    tree_result = classes[maxent_model.classify(RequestItem(words, '').features(all_words))]
    vector = vector_of_line(text, get_vector)
    features = [tree_result,
                get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "майнер_NOUN"),
                get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "расписание_NOUN"),
                get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "помощь_NOUN")]
    return target_names(decision_model.predict([features])[0])


while True:
    try:
        if __name__ == '__main__':
            now = datetime.now()
            today4am = now.replace(hour=4, minute=0, second=0, microsecond=0)
            if now == today4am:
                get_timetable()
            bot.polling(none_stop=True)
    except Exception as e:
        logger.error(e)
        time.sleep(15)