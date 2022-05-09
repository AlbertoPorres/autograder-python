FROM ubuntu:20.04

# desabilitar promp en la instalacion de paquetes
ARG DEBIAN_FRONTEND=noninteractive

# instalar pip3
RUN apt update && apt install -y python3-pip

WORKDIR /project

COPY . /project

RUN pip3 --no-cache-dir install -r requirements.txt

CMD ["python3", "src/app.py"]