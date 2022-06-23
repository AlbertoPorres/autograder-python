FROM ubuntu:20.04

# desabilitar promp en la instalacion de paquetes
ARG DEBIAN_FRONTEND=noninteractive

# instalar pip3
RUN apt update && apt install -y python3-pip python3-dev

WORKDIR /project

COPY . /project

# extensiones necesarias para el funcionamiento de Nbgrader
RUN pip3 --no-cache-dir install -r requirements.txt
RUN jupyter nbextension install --sys-prefix --py nbgrader --overwrite
RUN jupyter nbextension enable --sys-prefix --py nbgrader
RUN jupyter serverextension enable --sys-prefix --py nbgrader





