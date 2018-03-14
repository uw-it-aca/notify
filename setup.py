import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/notify>`_.
"""

# The VERSION file is created by travis-ci, based on the tag name
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
        'Django==1.11.10',
        'django-compressor',
        'django-templatetag-handlebars',
        'django-userservice>=1.3,<2.0',
        'django-aws-message>=0.2,<1.0',
        'unittest2',
        'python-dateutil',
        'AuthZ-Group>=1.6',
        'UW-RestClients-NWS>=0.82,<1.0',
        'UW-RestClients-SWS>=1.4.6.2,<2.0',
        'UW-RestClients-PWS>=0.6,<1.0',
        'UW-RestClients-GWS>=0.4.1,<1.0',
        'UW-RestClients-KWS>=0.1,<1.0',
        'UW-RestClients-Django-Utils>=0.6.9.1,<1.0',
        'Django-SupportTools>=1.2,<2.0',
        'django_mobileesp',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6'
    ],
)
