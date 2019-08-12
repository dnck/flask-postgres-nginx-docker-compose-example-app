#The Dockerfile is working in this ./web directory.
#Build the image with
#>> docker build -t <name> .
#and then run a container with,
#>> docker run -t -i <image_id>
#However, it breaks on looking for a connection to postgres.

FROM python:3.6

RUN mkdir /app

COPY . /app

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt

RUN python -m pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python", "run_service.py"]
