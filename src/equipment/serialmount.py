from platform import system

from serial import Serial
from decimal import Decimal

from typing import Tuple, Dict

import re

unix_port_re = re.compile(r'\/dev\/[a-zA-Z0-9\-]+')
win_port_re = re.compile(r'COM[0-9]')
serial_config_keys = ['port', 'baud_rate', 'data_bits', 'stop_bits', 'parity']
valid_parity_values = ['e', 'even', 'Even', 'n', 'none', 'None', 'o', 'odd', 'Odd']
valid_stop_bits = [0, 1, 2]


class SerialMount:
    _port: Serial = None
    _connected: bool = False
    _position: Tuple[Decimal, Decimal] = (0, 0)
    _config: dict = None

    def __init__(self, config: Dict, serial_port: Serial = None):
        self._config = config
        if serial_port is not None:
            self._port = serial_port
        else:
            self._port = Serial()

    @property
    def connected(self) -> bool:
        return self._port.is_open

    def connect(self) -> None:
        self._port.open()

    @staticmethod
    def validate_config(config: Dict) -> Tuple[bool, list]:
        has_error = False
        errors = []

        # validate serial port settings
        serial_config = config['serial']
        for key in serial_config_keys:
            if key not in serial_config:
                has_error = True
                errors.append(f'Key: {key} missing from mount serial config')
                continue

            os = system()

            value = serial_config[key]

            if key == 'port':
                if (os == 'Linux' or os == 'Darwin') and not re.match(unix_port_re, value):
                    has_error = True
                    errors.append(f'SerialMount Serial Port wrong format, expected \'/dev/XXX\' but was \'{value}\'')
                elif os == 'Windows' and not re.match(win_port_re, value):  # os == 'Windows'
                    has_error = True
                    errors.append(f'SerialMount Serial Port wrong format, expected \'COM<n>\' but was \'{value}\'')

            if key == 'baud_rate':
                if (type(value) is not int) or value < 9600 or value > 230400:
                    has_error = True
                    errors.append('SerialMount serial baud_rate must be an int between 9600 and 203400 inclusive')

            if key == 'data_bits':
                if (type(value) is not int) or value < 1 or value > 8:
                    has_error = True
                    errors.append('SerialMount serial data_bits must be an int between 1 and 8 inclusive')

            if key == 'parity':
                if (type(value) is not str) or value not in valid_parity_values:
                    has_error = True
                    errors.append(f'SerialMount serial parity must be one of [{",".join(valid_parity_values)}] but was \'{value}\'')

            if key == 'stop_bits':
                if (type(value) is not int) or value not in valid_stop_bits:
                    has_error = True
                    errors.append(f'SerialMount serial stop_bits must be an int one of [{",".join([str(x) for x in valid_stop_bits])}] but was \'{value}\'')

        return not has_error, errors
