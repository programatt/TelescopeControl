from abc import ABCMeta, abstractmethod, abstractproperty
from platform import system

from astropy.coordinates import EarthLocation
from serial import Serial
from serial.serialutil import (
    FIVEBITS,
    SIXBITS,
    SEVENBITS,
    EIGHTBITS,
    PARITY_EVEN,
    PARITY_NONE,
    PARITY_ODD,
    STOPBITS_ONE,
    STOPBITS_TWO,
    STOPBITS_ONE_POINT_FIVE
)
from decimal import Decimal

from typing import Tuple, Dict

import re

unix_port_re = re.compile(r'/dev/[a-zA-Z0-9\-]+')
win_port_re = re.compile(r'COM[1-9]')
required_serial_config_keys = ['port', 'baud_rate', 'data_bits', 'stop_bits', 'parity']
parity_value_map = {
    'e': PARITY_EVEN,
    'E': PARITY_EVEN,
    'even': PARITY_EVEN,
    'Even': PARITY_EVEN,
    'n': PARITY_NONE,
    'N': PARITY_NONE,
    'none': PARITY_NONE,
    'None': PARITY_NONE,
    'o': PARITY_ODD,
    'O': PARITY_ODD,
    'odd': PARITY_ODD,
    'Odd': PARITY_ODD
}
stop_bits_map = {
    1: STOPBITS_ONE,
    1.5: STOPBITS_ONE_POINT_FIVE,
    2: STOPBITS_TWO
}
data_bits_map = {
    5: FIVEBITS,
    6: SIXBITS,
    7: SEVENBITS,
    8: EIGHTBITS
}


class SerialMount(metaclass=ABCMeta):
    _port: Serial = None
    _position: EarthLocation = EarthLocation(0, 0, 0)
    _config: dict = None
    _polar_aligned: bool = False

    def __init__(self, config: Dict, serial_port: Serial = None):
        self._config = config
        if serial_port is None:
            self._port = Serial()
            valid, errors = SerialMount.validate_config(config)
            if valid:
                SerialMount.apply_config_to_serial_port(config, self._port)
            else:
                for msg in errors:
                    print(msg)
        else:
            self._port = serial_port

    @property
    def polar_aligned(self) -> bool:
        return self._polar_aligned

    @polar_aligned.setter
    def polar_aligned(self, value: bool) -> None:
        self._polar_aligned = value

    @property
    def connected(self) -> bool:
        return self._port.is_open

    @property
    @abstractmethod
    def position(self) -> EarthLocation:
        pass

    def connect(self) -> None:
        self._port.open()

    @staticmethod
    def apply_config_to_serial_port(config: Dict, port: Serial) -> None:
        port.port = config['serial']['port']
        port.baudrate = config['serial']['baud_rate']
        port.bytesize = config['serial']['data_bits']
        port.stopbits = stop_bits_map[config['serial']['stop_bits']]
        port.parity = parity_value_map[config['serial']['parity']]

    @staticmethod
    def validate_config(config: Dict) -> Tuple[bool, list]:
        has_error = False
        errors = []

        # validate serial port settings
        serial_config = config['serial']
        for key in required_serial_config_keys:
            if key not in serial_config:
                has_error = True
                errors.append(f'Key: {key} missing from mount serial config')
                continue

            os = system()
            value = serial_config[key]
            value_type = type(value)

            if key == 'port':
                if (os == 'Linux' or os == 'Darwin') and not re.match(unix_port_re, value):
                    has_error = True
                    errors.append(f'SerialMount Serial Port wrong format, expected \'/dev/XXX\' but was \'{value}\'')
                elif os == 'Windows' and not re.match(win_port_re, value):  # os == 'Windows'
                    has_error = True
                    errors.append(f'SerialMount Serial Port wrong format, expected \'COM<n>\' but was \'{value}\'')

            if key == 'baud_rate' and (value_type is not int or value < 9600 or value > 230400):
                has_error = True
                errors.append('SerialMount serial baud_rate must be an int between 9600 and 203400 inclusive')

            if key == 'data_bits' and (value_type is not int or value not in data_bits_map.keys()):
                has_error = True
                errors.append('SerialMount serial data_bits must be an int between 5 and 8 inclusive')

            if key == 'parity' and (value_type is not str or value not in parity_value_map.keys()):
                has_error = True
                errors.append(f'SerialMount serial parity must be one of [{",".join(parity_value_map.keys())}] but was \'{value}\'')

            if key == 'stop_bits' and value not in stop_bits_map.keys():
                has_error = True
                errors.append(f'SerialMount serial stop_bits must be an int one of [{",".join([str(x) for x in stop_bits_map.keys()])}] but was \'{value}\'')

        return not has_error, errors


class IoptronMount(SerialMount):

    def __init__(self, config: Dict, serial_port: Serial = None):
        super().__init__(config, serial_port)

