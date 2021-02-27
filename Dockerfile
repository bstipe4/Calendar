FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
RUN  apt-get install libpq-dev

COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt
WORKDIR /app

COPY . /app
EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
