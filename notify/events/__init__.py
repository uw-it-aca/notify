from notify.cache_implementation import UICache
from restclients_core.exceptions import DataFailureException
from aws_message.crypto import aes128cbc, Signature, CryptoException
from base64 import b64decode
from logging import getLogger
from uw_kws import KWS
import json
import re


class EventException(Exception):
    pass


class EventBase(object):
    _header = None
    _body = None

    def __init__(self, settings, message):
        self._kws = KWS()
        self._settings = settings
        self._re_guid = re.compile(
            r'^[\da-f]{8}(-[\da-f]{4}){3}-[\da-f]{12}$', re.I)
        self._re_json_cruft = re.compile(r'[^{]*({.*})[^}]*')
        self._log = getLogger('registration_consumer')

        try:
            self._header = message['Header']
            self._body = message['Body']
        except KeyError:
            self._header = {}
            self._body = message

        if ('MessageType' in self._header and
                self._header['MessageType'] != self._eventMessageType):
            raise EventException(
                'Unknown Message Type: %s' % (self._header['MessageType']))

    def validate(self):
        try:
            t = self._header['Version']
            if t != self._eventMessageVersion:
                raise EventException('Unknown Version: ' + t)

            to_sign = self._header['MessageType'] + '\n' \
                + self._header['MessageId'] + '\n' \
                + self._header['TimeStamp'] + '\n' \
                + self._body + '\n'

            sig_conf = {
                'cert': {
                    'type': 'url',
                    'reference': self._header['SigningCertURL']
                }
            }

            Signature(sig_conf).validate(to_sign.encode('ascii'),
                                         b64decode(self._header['Signature']))
        except KeyError as err:
            if len(self._header):
                raise EventException('Invalid Signature Header: %s' % (err))
        except CryptoException as err:
            raise EventException('Crypto: %s' % (err))
        except Exception as err:
            raise EventException('Invalid signature: %s' % (err))

    def extract(self):
        try:
            if 'Encoding' not in self._header:
                if isinstance(self._body, str):
                    return(json.loads(
                        self._re_json_cruft.sub(r'\g<1>', self._body)))
                elif isinstance(self._body, dict):
                    return self._body
                else:
                    raise EventException('No body encoding')

            t = self._header['Encoding']
            if str(t).lower() != 'base64':
                raise EventException('Unkown encoding: ' + t)

            t = self._header.get('Algorithm', 'aes128cbc')
            if str(t).lower() != 'aes128cbc':
                raise EventException('Unsupported algorithm: ' + t)

            key = None
            if 'KeyURL' in self._header:
                key = self._kws._key_from_json(
                    self._kws._get_resource(self._header['KeyURL']))
            elif 'KeyId' in self._header:
                key = self._kws.get_key(self._header['KeyId'])
            else:
                try:
                    key = self._kws.get_current_key(
                        self._header['MessageType'])
                    if not re.match(r'^\s*{.+}\s*$', self._body):
                        raise CryptoException()
                except (ValueError, CryptoException) as err:
                    UICache().delete_cached_kws_current_key(
                        self._header['MessageType'])
                    key = self._kws.get_current_key(
                        self._header['MessageType'])

            cipher = aes128cbc(b64decode(key.key),
                               b64decode(self._header['IV']))
            body = cipher.decrypt(b64decode(self._body))
            return (json.loads(self._re_json_cruft.sub(r'\g<1>', body)))

        except KeyError as err:
            self._log.error(
                "Key Error: %s\nHEADER: %s" % (err, self._header))
            raise
        except (ValueError, CryptoException) as err:
            raise EventException('Cannot decrypt: %s' % (err))
        except DataFailureException as err:
            msg = "Request failure for %s: %s (%s)" % (
                err.url, err.msg, err.status)
            self._log.error(msg)
            raise EventException(msg)
        except Exception as err:
            raise EventException('Cannot read: %s' % (err))

    def process(self):
        if self._settings.get('VALIDATE_MSG_SIGNATURE', True):
            self.validate()

        self.process_events(self.extract())

    def process_events(self, events):
        raise EventException('No event processor defined')
