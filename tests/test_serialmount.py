from astropy.coordinates import EarthLocation
import pytest
from platform import system
from serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from typing import Dict

from src.equipment.serialmount import SerialMount, parity_value_map, required_serial_config_keys
from unittest.mock import MagicMock, Mock, patch


class TestSerialMount(SerialMount):
    __test__ = False
    _position: EarthLocation = EarthLocation(0, 0, 0)

    def __init__(self, config, serial_port = None):
        super().__init__(config=config, serial_port=serial_port)

    @property
    def position(self):
        return self._position


def valid_config() -> Dict:
    return {
        'serial': {
            'port': 'COM1' if system() == 'Windows' else '/dev/cu.usbserial-TEST',
            'baud_rate': 115200,
            'data_bits': 8,
            'parity': 'none',
            'stop_bits': 1
        }
    }


def test_mount_not_connected_after_init():
    mount = TestSerialMount(config=valid_config())

    assert not mount.connected


def test_mount_connected_from_serial_port_is_open():
    port = Serial()
    port.open = Mock()
    port.is_open = MagicMock(return_value=True)
    mount = TestSerialMount(config={}, serial_port=port)

    mount.connect()

    assert mount.connected


def test_mount_config_valid():
    config = valid_config()

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid
    assert len(errors) == 0


@pytest.mark.parametrize("serial_key", required_serial_config_keys)
def test_validate_config_missing_required_serial_values(serial_key):
    config = valid_config()
    del config['serial'][serial_key]

    valid, errors = SerialMount.validate_config(config)

    assert not valid
    assert len(errors) == 1
    assert f'Key: {serial_key} missing from mount serial config' in errors


@pytest.mark.parametrize(
    "os,port,expected_valid,message",
    [
        ('Linux', '/dev/test', True, None),
        ('Darwin', '/dev/test', True, None),
        ('Windows', 'COM1', True, None),
        ('Linux', 'COM1', False, 'SerialMount Serial Port wrong format, expected \'/dev/XXX\' but was \'COM1\''),
        ('Darwin', 'COM1', False, 'SerialMount Serial Port wrong format, expected \'/dev/XXX\' but was \'COM1\''),
        ('Windows', '/dev/test', False, 'SerialMount Serial Port wrong format, expected \'COM<n>\' but was \'/dev/test\''),
    ])
@patch('src.equipment.serialmount.system')
def test_validate_config_serial_port_valid(system, os, port, expected_valid, message):
    system.return_value = os
    config = valid_config()
    config['serial']['port'] = port

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if is_valid:
        assert len(errors) == 0
    else:
        assert len(errors) == 1
        assert message in errors


@pytest.mark.parametrize('baud_rate,expected_valid', [
    (10000.0, False),
    (False, False),
    ('foo', False),
    (-1, False),
    (0, False),
    (9600, True),
    (230400, True),
    (230401, False),
])
def test_validate_config_baud_rate_is_integer_in_valid_range(baud_rate, expected_valid):
    config = valid_config()
    config['serial']['baud_rate'] = baud_rate

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if not is_valid:
        assert len(errors) == 1
        assert 'SerialMount serial baud_rate must be an int between 9600 and 203400 inclusive' in errors
    else:
        assert len(errors) == 0


@pytest.mark.parametrize('data_bits,expected_valid', [
    (10000.0, False),
    (False, False),
    ('foo', False),
    (-1, False),
    (4, False),
    (5, True),
    (6, True),
    (7, True),
    (8, True),
    (9, False),
])
def test_validate_config_data_bits(data_bits, expected_valid):
    config = valid_config()
    config['serial']['data_bits'] = data_bits

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if not is_valid:
        assert len(errors) == 1
        assert 'SerialMount serial data_bits must be an int between 5 and 8 inclusive' in errors
    else:
        assert len(errors) == 0


@pytest.mark.parametrize('parity', [
    1,
    1.1,
    False,
    {},
    None
])
def test_validate_config_parity_invalid_values(parity):
    config = valid_config()
    config['serial']['parity'] = parity

    valid, errors = SerialMount.validate_config(config)

    assert not valid
    assert len(errors) == 1
    assert f'SerialMount serial parity must be one of [e,E,even,Even,n,N,none,None,o,O,odd,Odd] but was \'{parity}\'' in errors


@pytest.mark.parametrize('parity', parity_value_map.keys())
def test_validate_config_parity_valid_values(parity):
    config = valid_config()
    config['serial']['parity'] = parity

    valid, errors = SerialMount.validate_config(config)

    assert valid
    assert len(errors) == 0


@pytest.mark.parametrize('stop_bits,expected_valid', [
    (False, False),
    ('foo', False),
    (-1, False),
    (0, False),
    (1, True),
    (1.5, True),
    (2, True),
    (3, False)
])
def test_validate_config_stop_bits(stop_bits, expected_valid):
    config = valid_config()
    config['serial']['stop_bits'] = stop_bits

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if not is_valid:
        assert len(errors) == 1
        assert f'SerialMount serial stop_bits must be an int one of [1,1.5,2] but was \'{stop_bits}\'' in errors


def test_serial_port_apply_config():
    config = valid_config()
    port = Serial()

    SerialMount.apply_config_to_serial_port(config, port)

    assert port.port == config['serial']['port']
    assert port.baudrate == config['serial']['baud_rate']
    assert port.bytesize == EIGHTBITS
    assert port.parity == PARITY_NONE
    assert port.stopbits == STOPBITS_ONE
