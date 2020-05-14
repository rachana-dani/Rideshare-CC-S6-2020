FROM python:3.7-slim-stretch
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN mkdir -p /code
COPY . /code
RUN pip install -r /code/requirements.txt
WORKDIR /code
EXPOSE 80
