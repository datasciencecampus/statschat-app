# Set base image (this loads the Debian Linux operating system)
FROM python:3.10.4-buster
ENV PYTHONUNBUFFERED True

# copy subset of files as specified by dockerignore
COPY . ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT 5000

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
