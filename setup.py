import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/notify>`_.
"""

version_path = 'notify/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

url = "https://github.com/uw-it-aca/notify"
setup(
    name='Notify.UW',
    version=VERSION,
    packages=['notify'],
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    include_package_data=True,
    install_requires=[
        'Django~=2.2',
        'django-compressor',
        'django-user-agents',
        'django-userservice~=3.1',
        'django-aws-message~=1.5',
        'psycopg2<2.9',
        'python-dateutil',
        'uw-memcached-clients~=1.0',
        'UW-Django-SAML2~=1.5',
        'UW-RestClients-NWS~=1.3',
        'UW-RestClients-SWS~=2.3',
        'UW-RestClients-PWS~=2.1',
        'UW-RestClients-KWS~=1.1',
        'UW-RestClients-Core~=1.3',
        'UW-RestClients-Django-Utils~=2.3',
        'Django-Persistent-Message',
        'Django-SupportTools~=3.5',
    ],
    license='Apache License, Version 2.0',
    description=('Notify.UW'),
    long_description=README,
    url=url,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6'
    ],
)
