FROM acait/django-container:1.0.22 as django

USER root
RUN apt-get update && apt-get install mysql-client libmysqlclient-dev libpq-dev -y
USER acait

ADD --chown=acait:acait notify/VERSION /app/notify/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/

RUN . /app/bin/activate && pip install -r requirements.txt

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/
RUN . /app/bin/activate && python manage.py collectstatic
