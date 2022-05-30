import os
import logging
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    encoding='UTF-8',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICT = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class WrongAPIResponseCodeError(Exception):
    """Исключение не правильного ответа API."""
    pass


class ConnectionError(Exception):
    """Исключение ошибки запроса API."""
    pass


class MissingKeysInDictionary(Exception):
    """Исключение нехватки ключа."""
    pass


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logger.info(f'Начинаем отправку сообщения в чат {TELEGRAM_CHAT_ID}')
    try:
        logger.info(f'Отправляем сообщения в чат {TELEGRAM_CHAT_ID}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(error, exc_info=True)
    finally:
        logger.info(
            f'Сообщение успешно отправленно в чат'
            f' {TELEGRAM_CHAT_ID}: {message}'
        )


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос и возвращает ответ API."""
    timestamp: int = current_timestamp or int(time.time())
    params: dict = {'from_date': timestamp}
    request_data: dict = {
        'url': ENDPOINT, 'headers': HEADERS, 'params': params
    }
    try:
        logger.info(f'Запрашиваем данные API у {ENDPOINT}')
        response: requests.models.Response = requests.get(**request_data)
        if response.status_code != HTTPStatus.OK:
            logger.error(f'Error {response.status_code}!')
            raise WrongAPIResponseCodeError(f'Error {response.status_code}!')
        return response.json()
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
        raise ConnectionError(f'Ошибка при запросе к API: {error}')


def check_response(response: dict) -> dict:
    """Проверяет ответ API и возвращает список домашних работ."""
    logger.info('Начинаем проверять ответ API')
    if not isinstance(response, dict):
        raise TypeError(f'API возвращает не словарь, а {type(response)}')
    list_works: list = response.get('homeworks')
    if not isinstance(list_works, list):
        raise TypeError(f'По ключу "homeworks" возвращается не список,'
                        f' а {type(response)}')
    if not all(k in response for k in ('homeworks', 'current_date')):
        logger.error('Отсутствуют ключи в словаре')
        raise MissingKeysInDictionary('Отсутствуют ключи в словаре')
    try:
        homework: dict = list_works[0]
        if not isinstance(homework, dict):
            raise TypeError(f'{type(homework)} - неверный тип данных.')
    except IndexError:
        logger.error('Список домашних работ пуст')
        raise IndexError('Список домашних работ пуст')
    return homework


def parse_status(homework: dict) -> str:
    """Извлекает из информации о домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise Exception('Отсутствует ключ "status" в ответе API')
    homework_name: str = homework['homework_name']
    homework_status: str = homework['status']
    if homework_status not in HOMEWORK_VERDICT:
        raise ValueError(f'Неизвестный статус работы: {homework_status}')
    verdict: str = HOMEWORK_VERDICT[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    list_tokens = all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    return list_tokens


def main():
    """Глобальная конфигурация для всех логгеров."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(funcName)s, %(lineno)s, %(levelname)s, %(message)s',
        encoding='UTF-8',
        filemode='w'
    )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    STATUS = ''
    ERROR_CACHE_MESSAGE = ''
    if not check_tokens():
        logger.critical(
            'Проверьте правильность заполнения этих токенов:'
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID'
        )
        sys.exit()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            message = parse_status(check_response(response))
            if message != STATUS:
                send_message(bot, message)
                STATUS = message
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error('Ошибка отправки сообщения в телеграмм')
            logger.error(error)
            message_t = str(error)
            if message_t != ERROR_CACHE_MESSAGE:
                send_message(bot, message_t)
                ERROR_CACHE_MESSAGE = message_t
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
