import requests
from xml.etree import ElementTree
import uuid

YANDEX_ASR_PATH = 'https://asr.yandex.net/asr_xml'
request_id = uuid.uuid4().hex
topic = 'queries'
VOICE_LANGUAGE = 'ru-RU'

from global_constants import YANDEX_API_KEY
from global_constants import token

requests.packages.urllib3.disable_warnings()


def speech_to_text(message, file_path):
    file_url = "https://api.telegram.org/file/bot{}/{}".format(
        token,
        file_path
    )
    xml_data = requests.post(
        "https://asr.yandex.net/asr_xml?uuid={}&key={}&topic={}&lang={}".format(
            request_id, YANDEX_API_KEY,
            topic,
            VOICE_LANGUAGE
        ),
        data=requests.get(file_url).content,
        headers={'Host': 'asr.yandex.net', "Content-type": 'audio/ogg;codecs=opus'}
    ).content
    e = ElementTree.fromstring(xml_data)
    if len(e) > 0:
        text = e[0].text
    else:
        raise SpeechException('Не удалось разобрать речь')

    if (not text):
        raise SpeechException('Не удалось разобрать речь')
    else:
        return text


class SpeechException(Exception):
    def __init__(self, message):
        self.message = message