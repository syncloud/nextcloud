FROM python:3.8-slim-buster
COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN rm -rf /var/lib/apt/lists/*