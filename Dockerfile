# Dockerfile for CCETD
FROM debian:8.6
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV CCETD_HOME /opt/ccetd/

RUN add-apt-repository ppa:fkrull/deadsnakes && \
    apt-get update && \
    apt-get -y install python3.5

COPY etd/ $CCETD_HOME/etd
COPY instance/ $CCETD_HOME/instance
COPY custom/ $CCETD_HOME/custom
COPY requirements.txt $CCETD_HOME/.

RUN cd $CCETD_HOME && \
    pip3 install -r requirements.txt &&

WORKDIR $CCETD_HOME
