from aws_message.processor import MessageBodyProcessor, ProcessorException
from aws_message.crypto import aes128cbc, Signature, CryptoException
from restclients_core.exceptions import DataFailureException
from notify.cache_implementation import UICache
from uw_kws import KWS
from logging import getLogger
from base64 import b64decode
import json
import re


class NotifyEventProcessor(MessageBodyProcessor):
    _re_json_cruft = re.compile(r'[^{]*({.*})[^}]*')

    def __init__(self, *args, **kwargs):
        super(NotifyEventProcessor, self).__init__(
            getLogger('registration_consumer'),
            self.QUEUE_SETTINGS_NAME,
            is_encrypted=True)

    def validate_message_body(self, message):
        header = message.get('Header', {})
        if ('MessageType' in header and
                header['MessageType'] != self._eventMessageType):
            raise ProcessorException(
                'Unknown Message Type: {}'.format(header['MessageType']))

        if ('Version' in header and
                header['Version'] != self._eventMessageVersion):
            raise ProcessorException(
                'Unknown Version: {}'.format(header['Version']))

        return True

    def _parse_signature(self, message):
        header = message['Header']
        to_sign = '{msgtype}\n{msgid}\n{timestamp}\n{body}\n'.format(
            msgtype=header['MessageType'], msgid=header['MessageId'],
            timestamp=header['TimeStamp'], body=message['Body'])

        sig_conf = {
            'cert': {
                'type': 'url',
                'reference': header['SigningCertURL']
            }
        }

        return (sig_conf, to_sign, header['Signature'])

    def validate_message_body_signature(self, message):
        try:
            (sig_conf, to_sign, signature) = self._parse_signature(message)
            Signature(sig_conf).validate(
                to_sign.encode('ascii'), b64decode(signature))

        except KeyError as ex:
            if len(header):
                raise ProcessorException(
                    'Invalid Signature Header: {}'.format(ex))
        except CryptoException as ex:
            raise ProcessorException('Cannot decode message: {}'.format(ex))
        except Exception as ex:
            raise ProcessorException(
                'Invalid signature {}: {}'.format(signature, ex))

    def decrypt_message_body(self, message):
        header = message['Header']
        body = message['Body']

        try:
            if 'Encoding' not in header:
                if isinstance(body, str):
                    return json.loads(self._re_json_cruft.sub(r'\g<1>', body))
                elif isinstance(body, dict):
                    return body
                else:
                    raise ProcessorException('No body encoding')

            encoding = header['Encoding']
            if str(encoding).lower() != 'base64':
                raise ProcessorException(
                    'Unkown encoding: {}'.format(encoding))

            algorithm = header.get('Algorithm', 'aes128cbc')
            if str(algorithm).lower() != 'aes128cbc':
                raise ProcessorException(
                    'Unsupported algorithm: {}'.format(algorithm))

            kws = KWS()
            key = None
            if 'KeyURL' in header:
                key = kws.get_key(url=header['KeyURL'])
            elif 'KeyId' in self._header:
                key = kws.get_key(key_id=self._header['KeyId'])
            else:
                try:
                    key = kws.get_current_key(header['MessageType'])
                    if not re.match(r'^\s*{.+}\s*$', body):
                        raise CryptoException()
                except (ValueError, CryptoException):
                    UICache().delete_cached_kws_current_key(
                        header['MessageType'])
                    key = kws.get_current_key(header['MessageType'])

            cipher = aes128cbc(b64decode(key.key), b64decode(header['IV']))
            body = cipher.decrypt(b64decode(body))

            return json.loads(
                self._re_json_cruft.sub(r'\g<1>', body.decode('utf-8')))

        except KeyError as ex:
            self.logger.error('Key Error: {}\nHEADER: {}'.format(ex, header))
            raise
        except ValueError as ex:
            self.logger.error(
                'Error: {}\nHEADER: {}\nBODY: {}'.format(ex, header, body))
            return {}
        except CryptoException as ex:
            self.logger.error(
                'Error: {}\nHEADER: {}\nBODY: {}'.format(ex, header, body))
            raise ProcessorException('Cannot decrypt: {}'.format(ex))
        except DataFailureException as ex:
            msg = 'Request failure for {}: {} ({})'.format(
                ex.url, ex.msg, ex.status)
            self.logger.error(msg)
            raise ProcessorException(msg)
        except Exception as ex:
            raise ProcessorException('Cannot read: {}'.format(ex))
