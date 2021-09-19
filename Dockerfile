FROM python:latest AS build
WORKDIR /app/
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt
COPY src/  /app/src
COPY environment/ /app/environment/
COPY scripts/ /app/scripts/
RUN chmod o+x /app/scripts/run/start.sh

FROM python:latest AS run
WORKDIR /app/
COPY --from=build /app/ ./
RUN pip3 install -r /app/requirements.txt
ENTRYPOINT ["/bin/bash","/app/scripts/run/start.sh"]


