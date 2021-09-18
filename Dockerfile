FROM python:latest AS build
WORKDIR /house-recommender/
COPY src/  /house-recommender/src
COPY requirements.txt /house-recommender/
RUN pip3 install -r requirements.txt
RUN ls -la
