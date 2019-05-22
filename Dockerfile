FROM python:3.6-alpine
WORKDIR /home
RUN /bin/sh -c '\
    apk add --no-cache gcc musl-dev python3-dev postgresql-dev \
    && python -m pip install --upgrade pip \
    && python -m pip install virtualenv \
    && python -m virtualenv virtualenv \
    && source virtualenv/bin/activate \
    && pip install psycopg2'
ENV FLASK_ENV="production" FLASK_APP="animeu.app"
EXPOSE 5000
COPY requirements.txt .
RUN /bin/sh -c '\
    source virtualenv/bin/activate \
    && pip install -r requirements.txt \
    && pip install gunicorn'
COPY . .
RUN /bin/sh -c 'pip install -e .'
CMD /bin/sh -c '\
    source virtualenv/bin/activate && \
    flask db upgrade && \
    gunicorn -w 4 -b "0.0.0.0:${PORT:-5000}" animeu.app:app'
