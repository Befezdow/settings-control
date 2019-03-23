# works on ubuntu 16.04 with commands here and fixes in LegacyWireless.py file.
import time
from configuration.wireless import LegacyWireless, cmd

interface_name = 'wlp3s0'
password = '+78312171590'
wire = LegacyWireless(interface_name)

print(cmd('nmcli con show'))
wire.connect(ssid='Silencium', password='KSpeoq')
old_connection = wire.current()
print(cmd('nmcli con show'))
time.sleep(4)

if not wire.connect(ssid='STM', password=password + '2'):
    print('Error while connecting to network!')
    # wire.power(power=False)
    # wire.power(power=True)

print(cmd('nmcli con show'))
print(cmd('nmcli con up {}'.format(old_connection)))
print(wire.current())
