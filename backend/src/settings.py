from src.singleton import Singleton
from src.logger import Logger
import json
import os


class Settings(metaclass=Singleton):
    def __init__(self, config_path=os.getcwd() + '/config.conf'):
        self.config_path = config_path
        self.config = {}
        self.server_config = {}
        self.load_config()

    def load_config(self):
        Logger().info_message('Loading config')
        try:
            config_file = open(self.config_path, 'r')
            self.config = json.loads(config_file.read())
        except Exception as ex:
            Logger().error_message('Loading config error: {}'.format(str(ex)))
        Logger().info_message('Config successfully loaded')

    def load_current_server_config(self):
        Logger().info_message('Loading config for {} from {}'.format(self.config['type'], self.config['server_config']))
        if not self.server_config:
            try:
                config_file = open(self.config['server_config'], 'r')
                self.server_config = json.loads(config_file.read())
            except Exception as ex:
                Logger().error_message('Loading config error: {}'.format(str(ex)))
        return self.server_config


