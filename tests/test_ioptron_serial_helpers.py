from astropy.coordinates import EarthLocation
from re import compile


def test_convert_location_to_earthlocation():
    response = ""

    location = response_to_earthlocation(response)

    pass


status_msg_re = compile(r'')


def response_to_earthlocation(response: str) -> EarthLocation:
    pass
