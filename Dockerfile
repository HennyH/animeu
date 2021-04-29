FROM python:stretch
WORKDIR /usr/src/app

RUN pip install --user https://github.com/rogerbinns/apsw/releases/download/3.35.4-r1/apsw-3.35.4-r1.zip \
    --global-option=fetch --global-option=--version --global-option=3.35.4 --global-option=--all \
    --global-option=build --global-option=--enable-all-extensions
RUN pip install psycopg2
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN /bin/sh -c 'pip install -e .'

ENV FLASK_ENV="production"
ENV FLASK_APP="animeu.app"
ENV DATA_FILE="characters.json"
ENV DATABASE="sqlite:///usr/src/app/app.db"
EXPOSE 80

CMD /bin/sh -c '\
    flask db upgrade && \
    gunicorn -w 4 -b "0.0.0.0:${PORT:-80}" animeu.app:app'
