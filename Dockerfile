FROM python:3.6-alpine
WORKDIR /home
ENV FLASK_ENV="production" FLASK_APP="animeu.app"
EXPOSE 5000
RUN /bin/sh -c '\
    python -m pip install --upgrade pip \
    && python -m pip install virtualenv \
    && python -m virtualenv virtualenv'
COPY . .
RUN /bin/sh -c 'source virtualenv/bin/activate && pip install -e .'
RUN adduser -D animeu
USER animeu
CMD /bin/sh -c '\
    source /home/virtualenv/bin/activate \
    && flask db upgrade \
    && flask run --host 0.0.0.0 --port ${PORT:-5000}'
