# Dockerfile for CCETD
FROM debian:jessie-slim
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV CCETD_HOME /opt/ccetd/

RUN apt-get update && \
    apt-get install -y libssl-dev openssl wget gcc make && \
    wget https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz && \
    tar xzvf Python-3.5.2.tgz && cd Python-3.5.2 && \
    ./configure && make && make install 

COPY etd/ $CCETD_HOME/etd
COPY instance/ $CCETD_HOME/instance
COPY custom/ $CCETD_HOME/custom
COPY requirements.txt $CCETD_HOME/.
COPY run.py $CCETD_HOME/.

RUN cd $CCETD_HOME && \
    pip3 install -r requirements.txt 

WORKDIR $CCETD_HOME

CMD ["nohup", "gunicorn", "-w 2", "-b :8084", "run:parent_app", "&"]
