from abc import ABCMeta, abstractmethod
import subprocess
from time import sleep
from packaging import version
from support.singleton import Singleton
from support.server_exception import ServerException
from flask_api import status
# set static ip:  nmcli con modify wireless_clone ipv4.addresses 192.168.1.100/24 ipv4.method manual
# ipv4.gateway 192.168.1.1 ipv4.dns 8.8.4.4 && nmcli con down wireless_clone && nmcli con up wireless_clone


# send a command to the shell and return the result
def cmd(command):
    return subprocess.Popen(
        command, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.read().decode()


# abstracts class of Wifi configurator
class NetworkService(metaclass=Singleton):
    _driver_name = None
    _driver = None

    # init
    def __init__(self, interface_wifi=None, interface_eth=None):
        # detect and init appropriate driver
        self._driver_name = self._detect_driver()
        if self._driver_name == 'nmcli0990':
            self._driver = NewNmcli0990(interface_wifi=interface_wifi, interface_eth=interface_eth)

        # attempt to auto detect the wifi interface if none was provided
        if self.interface_wifi() is None:
            interfaces = self.interfaces_wifi()
            if interfaces:
                self.interface_wifi(interfaces[0])

        # attempt to auto detect the ethernet interface if none was provided
        if self.interface_eth() is None:
            interfaces = self.interfaces_eth()
            if interfaces:
                self.interface_eth(interfaces[0])

        # raise an error if there is still no interface defined
        if self.interface_wifi() is None and self.interface_eth() is None:
            raise Exception('Не удалось найти ни одного сетевого интерфейса')

    @staticmethod
    def _detect_driver():
        # try nmcli (Ubuntu 14.04, 16.04, 18.04)
        response = cmd('which nmcli')
        if len(response) > 0 and 'not found' not in response:
            response = cmd('nmcli --version')
            parts = response.split()
            ver = parts[-1]
            print(ver)
            if version.parse(ver) > version.parse('0.9.9.0'):
                return 'nmcli0990'
            else:
                return 'nmcli'

        raise Exception('Unable to find compatible nmcli driver.')

    def connection_up(self, uuid):
        return self._driver.connection_up(uuid)

    def connection_down(self, uuid):
        return self._driver.connection_down(uuid)

    def create_wifi_connection(self, ssid, password):
        return self._driver.create_wifi_connection(ssid, password)

    def delete_connection(self, uuid):
        return self._driver.delete_connection(uuid)

    def modify_connection_params(self, uuid, params_dict):
        return self._driver.modify_connection_params(uuid, params_dict)

    # uuid of current wi-fi connection
    def current_wifi(self):
        return self._driver.current_wifi()

    # uuid of current eth connection
    def current_eth(self):
        return self._driver.current_eth()

    def interfaces_wifi(self):
        return self._driver.interfaces_wifi()

    def interfaces_eth(self):
        return self._driver.interfaces_eth()

    # return the current wireless adapter
    def interface_wifi(self, interface=None):
        return self._driver.interface_wifi(interface)

    def interface_eth(self, interface=None):
        return self._driver.interface_eth(interface)

    # return the current wireless adapter
    def power_wifi(self, power=None):
        return self._driver.power_wifi(power)

    # return the driver name
    def driver(self):
        return self._driver_name

    def list_of_connections(self, rescan_wifi=True):
        return self._driver.list_of_connections(rescan_wifi)


# abstract class for all wifi drivers
class NetworkDriver(metaclass=ABCMeta):

    @abstractmethod
    def connect(self, ssid, password):
        pass

    @abstractmethod
    def current_wifi(self):
        pass

    @abstractmethod
    def current_eth(self):
        pass

    @abstractmethod
    def interfaces_wifi(self):
        pass

    @abstractmethod
    def modify_connection_params(self, uuid, params_dict):
        pass

    @abstractmethod
    def create_wifi_connection(self, ssid, password):
        pass

    @abstractmethod
    def connection_up(self, uuid):
        pass

    @abstractmethod
    def connection_down(self, uuid):
        pass

    @abstractmethod
    def delete_connection(self, uuid):
        pass

    @abstractmethod
    def interfaces_eth(self):
        pass

    @abstractmethod
    def interface_wifi(self, interface=None):
        pass

    @abstractmethod
    def interface_eth(self, interface=None):
        pass

    @abstractmethod
    def power_wifi(self, power=None):
        pass

    @abstractmethod
    def list_of_connections(self, rescan_wifi=True):
        pass


# Linux nmcli Driver >= 0.9.9.0 (Actual driver)
class NewNmcli0990(NetworkDriver):
    _interface_wifi = None
    _interface_eth = None

    # init
    def __init__(self, interface_wifi=None, interface_eth=None):
        self.interface_wifi(interface_wifi)
        self.interface_eth(interface_eth)
        # TODO persist
        self.ssid_to_uuid = self._load_connection_map()

    def _save_connection_map(self):
        import json
        with open('settings_tool_backend_connection_map', 'w') as f:
            f.write(json.dumps(self.ssid_to_uuid))
        return True

    def _load_connection_map(self):
        import json
        with open('settings_tool_backend_connection_map', 'r') as f:
            json_data = f.read()
            if json_data:
                return json.loads(json_data)
        return {}

    # clean up connections where partial is part of the connection name
    # this is needed to prevent the following error after extended use:
    # 'maximum number of pending replies per connection has been reached'
    @staticmethod
    def _clean(partial):
        # list matching connections
        # TODO check what will be if we delete last wired connection?
        command = 'nmcli -t -f UUID,NAME con show | grep wireless'
        if partial:
            command + ' | grep {}'.format(partial)
        response = cmd(command)

        # delete all of the matching connections
        for line in response.splitlines():
            if line:
                uuid = line.split(':')[0]
                cmd('nmcli con delete {}'.format(uuid))

    # ignore warnings in nmcli output
    # sometimes there are warnings but we connected just fine
    @staticmethod
    def _error_in_response(response):
        # no error if no response
        if not response:
            return False

        # loop through each line
        for line in response.splitlines():
            # all error lines start with 'Error'
            if line.startswith('Error'):
                return True

        # if we didn't find an error then we are in the clear
        return False

    def _get_wifi_list(self):
        response = cmd('nmcli -t -f SSID,MODE,CHAN,FREQ,RATE,SIGNAL,SECURITY,DEVICE,ACTIVE dev wifi list')
        if self._error_in_response(response):
            raise ServerException('Не удалось получить список беспроводных соеденений. Ответ команды: {}'
                                  .format(response), status.HTTP_500_INTERNAL_SERVER_ERROR)
        connections = response.splitlines()
        mapped = []
        for connection in connections:
            splitted_array = connection.split(':')
            mapped.append({
                'name': splitted_array[0],
                'id': self.ssid_to_uuid.get(splitted_array[0]),
                'type': 'wifi',
                'mode': splitted_array[1],
                'channel': splitted_array[2],
                'frequency': splitted_array[3],
                'speed_rate': splitted_array[4],
                'signal_level': splitted_array[5],
                'security_type': splitted_array[6],
                'device': splitted_array[7],
                'active': splitted_array[8] == 'yes',
                # TODO may be add in map by ssid 'autoconnect': splitted_array[5] == 'yes'
            })
        return mapped

    def _get_eth_list(self):
        response = cmd('nmcli -t -f NAME,UUID,TYPE,DEVICE,ACTIVE,AUTOCONNECT con show | grep ethernet')
        if self._error_in_response(response):
            raise ServerException('Не удалось получить список проводных соеденений. Ответ команды: {}'.format(response))
        connections = response.splitlines()
        mapped = []
        for connection in connections:
            splitted_array = connection.split(':')
            mapped.append({
                'name': splitted_array[0],
                'id': splitted_array[1],
                'type': 'eth',
                'device': splitted_array[3],
                'active': splitted_array[4] == 'yes',
                'autoconnect': splitted_array[5] == 'yes'
            })
        return mapped

    def connection_up(self, uuid):
        response = cmd('nmcli con up {}'.format(uuid))
        if self._error_in_response(response):
            if 'unknown connection' in response:
                raise ServerException('Неизвестный идентификатор соединения {}'.format(uuid), status.HTTP_400_BAD_REQUEST)
            elif 'device could not be readied' in response:
                raise ServerException('Не удалось активировать соединение. Девайс недоступен', status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # TODO add logger
                raise ServerException('Серверная ошибка', status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    def connection_down(self, uuid):
        response = cmd('nmcli con down {}'.format(uuid))
        if self._error_in_response(response):
            if 'unknown connection' in response:
                raise ServerException('Неизвестный идентификатор соединения {}'.format(uuid),
                                      status.HTTP_400_BAD_REQUEST)
            elif 'device could not be readied' in response:
                raise ServerException('Не удалось активировать соединение. Девайс недоступен',
                                      status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # TODO add logger
                raise ServerException('Серверная ошибка', status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    def delete_connection(self, uuid):
        # TODO test
        response = cmd('nmcli con delete {}'.format(uuid))
        if self._error_in_response(response):
            if 'unknown connection' in response:
                raise ServerException('Неизвестный идентификатор соединения {}'.format(uuid),
                                      status.HTTP_400_BAD_REQUEST)
            else:
                # TODO add logger
                raise ServerException('Серверная ошибка', status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    def current_wifi(self):
        # list active connections for all interfaces
        response = cmd('nmcli -t -f UUID,TYPE con show --active | grep wireless')

        # the current network is in the first column
        for line in response.splitlines():
            if line:
                return line.split(':')[0]

        # return none if there was not an active connection
        return None

    def current_eth(self):
        # list active connections for all interfaces
        response = cmd('nmcli -t -f UUID,TYPE con show --active | grep ethernet')

        # the current network is in the first column
        for line in response.splitlines():
            if line:
                return line.split(':')[0]

        # return none if there was not an active connection
        return None

    def modify_connection_params(self, uuid, params_dict):
        params_string = ''
        for key in params_dict:
            params_string += '{} {}'.format(key, params_dict[key])
        command = 'nmcli con modify {} {} && nmcli && nmcli con up {}'.format(uuid, params_string, uuid)
        response = cmd(command)
        if self._error_in_response(response):
            # TODO check error type
            raise ServerException(response, status.HTTP_400_BAD_REQUEST)
        else:
            # trying to fetch uuid from response from nmcli
            return True

    def create_wifi_connection(self, ssid, password):
        # clean up previous connection TODO check for need of it
        # self._clean(ssid)
        # turn off current connection
        current_wifi_id = self.current_wifi()
        if current_wifi_id:
            cmd('nmcli con down {}'.format(current_wifi_id))
        # trying to connect
        response = cmd('nmcli dev wifi connect {} password {} iface {}'.format(
            ssid, password, self._interface_wifi))
        # parse response
        # TODO if error need to up old connection or autoconnect?
        if self._error_in_response(response):
            # TODO check error type invalid password or smth another
            raise ServerException(response, status.HTTP_400_BAD_REQUEST)
        else:
            # trying to fetch uuid from response from nmcli
            uuid = response.split(' ')[-1].replace("'", '').replace('.', '')
            self.ssid_to_uuid[ssid] = uuid
            self._save_connection_map()
            return True

    def list_of_connections(self, rescan_wifi=True):
        if rescan_wifi and self.interface_wifi() is not None:
            res = ''
            while 'immediately' not in res:
                res = cmd('nmcli dev wifi rescan')
                sleep(0.5)
            sleep(1)

        return {
            'wired': self._get_eth_list(),
            'wireless': self._get_wifi_list()
        }

    def interfaces_wifi(self):
        # grab list of interfaces
        response = cmd('nmcli -t dev | grep wifi')

        # parse response
        interfaces = []
        for line in response.splitlines():
            # this line has our interface name in the first column
            interfaces.append(line.split(':')[0])

        # return list
        return interfaces

    def interfaces_eth(self):
        # grab list of interfaces
        response = cmd('nmcli -t dev | grep ethernet')

        # parse response
        interfaces = []
        for line in response.splitlines():
            # this line has our interface name in the first column
            interfaces.append(line.split(':')[0])

        # return list
        return interfaces

    # TODO refactor to get\set
    # return the current wireless adapter
    def interface_wifi(self, interface=None):
        if interface is not None:
            self._interface_wifi = interface
        else:
            return self._interface_wifi

    def interface_eth(self, interface=None):
        if interface is not None:
            self._interface_eth = interface
        else:
            return self._interface_eth

    def connect(self, ssid, password):
        pass

    # TODO refactor to get\set
    def power_wifi(self, power=None):
        if power is True:
            cmd('nmcli r wifi on')
        elif power is False:
            cmd('nmcli r wifi off')
        else:
            if self.interface_wifi() is not None:
                response = cmd('nmcli r wifi')
                return 'enabled' in response
            else:
                return False


if __name__ == '__main__':
    uuid = 'aaaa'
    params = {
        'ipv4.addresses': '192.168.1.100/24',
        'ipv4.method': 'manual',
        'ipv4.gateway': '192.168.1.1',
        'ipv4.dns': '8.8.4.4'
    }
    print(NetworkService().list_of_connections())
    print('Changed connection params result: {}'.format(NetworkService().modify_connection_params(uuid, params)))
