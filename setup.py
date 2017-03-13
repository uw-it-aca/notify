import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/notify>`_.
"""

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

url = "https://github.com/uw-it-aca/notify"
setup(
    name='Notify.UW',
    version='1.0',
    packages=['notify'],
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    include_package_data=True,
    install_requires=[
        'Django==1.10.5',
        'django-compressor',
        'django-templatetag-handlebars',
        'django-userservice==1.2.1',
        'unittest2',
        'AuthZ-Group',
        'UW-RestClients==1.6.2',
        'Django-SupportTools',
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
    ],
)

