FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /flask_app
WORKDIR /flask_app
EXPOSE 5000
COPY requirements.txt /flask_app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /flask_app/
CMD [ "uwsgi", "--ini", "app.ini" ]
