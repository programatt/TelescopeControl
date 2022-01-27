import pytest
from platform import system
from serial import Serial

from src.equipment.serialmount import SerialMount, valid_parity_values, serial_config_keys
from unittest.mock import MagicMock, Mock, patch


def valid_config() -> dict:
    return {
        'serial': {
            'port': 'COM1' if system() == 'Windows' else '/dev/cu.usbserial-TEST',
            'baud_rate': 115200,
            'data_bits': 8,
            'parity': 'none',
            'stop_bits': 1
        }
    }


def test_mount_not_connected():
    mount = SerialMount(config={})

    assert not mount.connected


#  TODO Should be run when the mount is connected
def test_mount_connected():
    port = Serial()
    port.open = Mock()
    port.is_open = MagicMock(return_value=True)
    mount = SerialMount(config={}, serial_port=port)

    mount.connect()

    assert mount.connected


def test_mount_config_valid():
    config = valid_config()

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid
    assert len(errors) == 0


@pytest.mark.parametrize("serial_key", serial_config_keys)
def test_validate_config_missing_serial_values(serial_key):
    config = valid_config()
    del config['serial'][serial_key]

    valid, errors = SerialMount.validate_config(config)

    assert not valid
    assert f'Key: {serial_key} missing from mount serial config' in errors
    assert len(errors) == 1


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
    if not is_valid:
        assert message in errors
        assert len(errors) == 1


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
def test_validate_config_baud_rate_is_integer_greater_than_minimum(baud_rate, expected_valid):
    config = valid_config()
    config['serial']['baud_rate'] = baud_rate

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if not is_valid:
        assert 'SerialMount serial baud_rate must be an int between 9600 and 203400 inclusive' in errors
        assert len(errors) == 1


@pytest.mark.parametrize('data_bits,expected_valid', [
    (10000.0, False),
    (False, False),
    ('foo', False),
    (-1, False),
    (0, False),
    (1, True),
    (8, True),
    (9, False),
])
def test_validate_config_data_bits(data_bits, expected_valid):
    config = valid_config()
    config['serial']['data_bits'] = data_bits

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if not is_valid:
        assert 'SerialMount serial data_bits must be an int between 1 and 8 inclusive' in errors
        assert len(errors) == 1


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
    assert f'SerialMount serial parity must be one of [e,even,Even,n,none,None,o,odd,Odd] but was \'{parity}\'' in errors
    assert len(errors) == 1


@pytest.mark.parametrize('parity', valid_parity_values)
def test_validate_config_parity_valid_values(parity):
    config = valid_config()
    config['serial']['parity'] = parity

    valid, errors = SerialMount.validate_config(config)

    assert valid
    assert len(errors) == 0


@pytest.mark.parametrize('stop_bits,expected_valid', [
    (10000.0, False),
    (False, False),
    ('foo', False),
    (-1, False),
    (0, True),
    (1, True),
    (2, True),
    (3, False),
])
def test_validate_config_stop_bits(stop_bits, expected_valid):
    config = valid_config()
    config['serial']['stop_bits'] = stop_bits

    is_valid, errors = SerialMount.validate_config(config)

    assert is_valid == expected_valid
    if not is_valid:
        assert f'SerialMount serial stop_bits must be an int one of [0,1,2] but was \'{stop_bits}\'' in errors
        assert len(errors) == 1
