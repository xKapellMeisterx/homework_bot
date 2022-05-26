import os
import logging
from datetime import time
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message):
    return bot.send_message(TELEGRAM_CHAT_ID, message)


current_timestamp = int(time.time())


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time)
    params = {'from_date': 0}
    valid_json = dict()
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        valid_json = response.json()
    except requests.ConnectionError:
        message = 'Ошибка соединения.'
        logger.error(message)
        send_message(message)
    return valid_json['homeworks'][0]

# def check_response(response):
#
#     ...

def parse_status(homework):
    homework_name = homework.get('homework_name', 'Нет имени работы')
    print(homework_name)
    try:
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        return (f'На за')
    return f'Изменился статус проверки работы "{homework_name}". \n{verdict}'


print(parse_status(get_api_answer(current_timestamp)))

# def check_tokens():
#     ...


# def main():
#     """Основная логика работы бота."""
#
#     ...
#
#     bot = telegram.Bot(token=TELEGRAM_TOKEN)
#     current_timestamp = int(time.time())
#
#     ...
#
#     while True:
#         try:
#             response = ...
#
#             ...
#
#             current_timestamp = ...
#             time.sleep(RETRY_TIME)
#
#         except Exception as error:
#             message = f'Сбой в работе программы: {error}'
#             ...
#             time.sleep(RETRY_TIME)
#         else:
#             ...
#
#
# if __name__ == '__main__':
#     main()
