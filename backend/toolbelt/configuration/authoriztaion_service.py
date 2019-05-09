from toolbelt.support.singleton import Singleton
from toolbelt.support.settings_service import SettingsService
from flask import flash
import base64
from flask_api import status
import uuid
from toolbelt.support.server_exception import ServerException
import datetime


class AuthorizationService(metaclass=Singleton):
    def __init__(self):
        self.token_uuid = None
        self.last_token_use = None

    def _check_password(self, password):
        stored_pass = SettingsService().server_config.get('password')
        if not stored_pass:
            err_text = 'Ошибка аутентификации. Проверьте пароль на сервере'
            flash(err_text)
            raise ServerException(err_text, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return password == stored_pass

    def _generate_token(self, password):
        token_uuid = str(uuid.uuid4())
        token = 'Basic {}'.format(base64.b64encode('{}:{}'.format(token_uuid, password).encode()).decode('utf-8'))
        self.token_uuid = token_uuid
        return token

    def _is_token_expired(self):
        now = datetime.datetime.now()
        expiration_time = SettingsService().server_config.get('token_expiration_time')
        return ((now - self.last_token_use).seconds / 60) > expiration_time

    def authorize(self, password):
        if self._check_password(password):
            self.last_token_use = datetime.datetime.now()
            return self._generate_token(password)
        else:
            err_text = 'Неправильный пароль'
            flash(err_text)
            raise ServerException(err_text, status.HTTP_401_UNAUTHORIZED)

    def deauthorize(self):
        if self.token_uuid:
            self.token_uuid = None
            return True
        else:
            err_text = 'Токен не найден, необходимо авторизироваться'
            flash(err_text)
            raise ServerException(err_text, status.HTTP_401_UNAUTHORIZED)

    def check_token(self, token_uuid, password):
        if self.token_uuid:
            token_correct = self.token_uuid == token_uuid
            if not token_correct:
                err_text = 'Токен не найден, необходимо авторизироваться'
                flash(err_text)
                raise ServerException(err_text, status.HTTP_401_UNAUTHORIZED)

            if self._check_password(password):
                if not self._is_token_expired():
                    self.last_token_use = datetime.datetime.now()
                    return True
                else:
                    return False
            else:
                err_text = 'Неправильный пароль'
                flash(err_text)
                raise ServerException(err_text, status.HTTP_401_UNAUTHORIZED)
        else:
            err_text = 'Токен не найден, необходимо авторизироваться'
            flash(err_text)
            raise ServerException(err_text, status.HTTP_401_UNAUTHORIZED)

    def change_password(self, old_password, new_password):
        stored_pass = SettingsService().server_config.get('password')
        if not stored_pass:
            err_text = 'Ошибка аутентификации. Проверьте пароль на сервере'
            flash(err_text)
            raise ServerException(err_text, status.HTTP_500_INTERNAL_SERVER_ERROR)

        if old_password == stored_pass:
            SettingsService().server_config['password'] = new_password
            SettingsService().save_server_config()
            self.last_token_use = datetime.datetime.now()
            return self._generate_token(new_password)
        else:
            err_text = 'Неправильный пароль'
            flash(err_text)
            raise ServerException(err_text, status.HTTP_401_UNAUTHORIZED)
