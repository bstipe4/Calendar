#FROM python:3.9-alpine
#
#ENV PYTHONUNBUFFERED 1
#
#
#COPY ./requirements.txt /requirements.txt
#
#RUN apk add --update --no-cache postgresql-client
#RUN apk add --update --no-cache --virtual .tmp-build-deps \
#	gcc libc-dev linux-headers postgresql-dev
#RUN pip install -r /requirements.txt
#
#RUN apk del .tmp-build-deps
#
#RUN mkdir /app
#WORKDIR /app
#COPY . /app
#
#RUN adduser -D user
#USER user
#
#EXPOSE 80
#
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]


FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
RUN  apt-get install libpq-dev
RUN pip install fastapi uvicorn psycopg2 sqlalchemy
COPY ./app /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
