FROM python
label org.opencontainers.image.source = "https://github.com/Tweeticoats/stashdb-tools"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY . /app
WORKDIR /app

CMD [ "gunicorn","--bind=0.0.0.0:5555","wsgi:app"]
