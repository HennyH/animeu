FROM python:3.6.8-stretch
WORKDIR /home
RUN /bin/bash -c '\
    python -m pip install --upgrade pip \
    && python -m pip install virtualenv \
    && python -m virtualenv virtualenv'
COPY . .
RUN /bin/bash -c 'source virtualenv/bin/activate && pip install -e .'
EXPOSE 5000
ENV FLASK_ENV="production" FLASK_APP="animeu.app"
ENTRYPOINT [ "/home/run.sh" ]
