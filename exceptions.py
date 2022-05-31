class WrongAPIResponseCodeError(Exception):
    """Исключение не правильного ответа API."""
    pass


class ConnectionError(Exception):
    """Исключение ошибки запроса API."""
    pass


class MissingKeysInDictionary(Exception):
    """Исключение нехватки ключа."""
    pass
