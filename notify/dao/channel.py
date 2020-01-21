from django.conf import settings
from uw_nws import NWS
import dateutil.parser

CHANNEL_TYPE = 'uw_student_courseavailable'


def channel_expires():
    expires = getattr(settings, 'CHANNEL_EXPIRES_AFTER', None)
    if expires is not None:
        expires = dateutil.parser.parse(expires)
    return expires


def get_channel_by_id(channel_id):
    return NWS().get_channel_by_channel_id(channel_id)


def get_active_channels_by_year_quarter(year, quarter):
    return NWS().get_active_channels_by_year_quarter(
        CHANNEL_TYPE, year, quarter, expires=channel_expires())


def get_channel_by_sln_year_quarter(sln, year, quarter):
    channels = NWS().get_channels_by_sln_year_quarter(
        CHANNEL_TYPE, sln, year, quarter)
    if len(channels):
        return channels[0]
