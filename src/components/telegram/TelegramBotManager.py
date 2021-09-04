import requests
from enum import Enum


class RequestType(Enum):
    SEND_MESSAGE = 1


class TelegramBotManager:

    _configuration = None
    _bot_token = None
    _bot_chat_id = None
    _base_url = 'https://api.telegram.org/bot'

    def __init__(self, configuration):
        self._configuration = configuration
        if 'bot_token' in configuration:
            self._bot_token = configuration['bot_token']
        if 'bot_chat_id' in configuration:
            self._bot_chat_id = configuration['bot_chat_id']
        if 'base_url' in configuration:
            self._base_url = configuration['base_url']

    # Supports only markdown for now
    def _build_request(self, request_type, args ):
        if request_type == RequestType.SEND_MESSAGE:
            method_name = 'sendMessage'
            message = args['text_message']
            chat_id = args['chat_id']
            base_url = f'{self._base_url}{self._bot_token}/{method_name}?chat_id={chat_id}&parse_mode=Markdown&text={message}'
            return base_url
        else:
            raise ValueError(f'The value {request_type} is not valid')

    # Bulkified for the user but use one by one for now.
    def send_text_message_to_users(self, message, chat_ids=None):
        responses = []
        request_args = {'text_message': message}
        chat_id_list = chat_ids.split(',') if chat_ids else [self._bot_chat_id]
        for chat_id in chat_id_list:
            request_args['chat_id'] = chat_id
            request_url = self._build_request(RequestType.SEND_MESSAGE, request_args)
            response = requests.get(request_url)
            responses.append(response)
            print(response.status_code)

        return responses
