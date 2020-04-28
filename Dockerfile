FROM acait/django-container:1.0.24 as notify-container

USER root
RUN apt-get update && apt-get install libpq-dev -y
USER acait

ADD --chown=acait:acait notify/VERSION /app/notify/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/
ADD --chown=acait:acait db.sqlite3 /app/

RUN . /app/bin/activate && pip install -r requirements.txt

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/
RUN . /app/bin/activate && python manage.py collectstatic

FROM acait/django-test-container:1.0.26 as notify-test-container

COPY --from=0 /app/ .
