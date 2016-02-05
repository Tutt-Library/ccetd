FROM python:3.5.1
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV CCETD_GIT https://github.com/Tutt-Library/ccetd.git
ENV CCETD_HOME /opt/ccetd
ENV CCETD_CONF instance/conf.py

RUN apt-get update && apt-get install -y && \
  apt-get install -y python3-setuptools && \
  apt-get install -y python3-pip

RUN git clone $CCETD_GIT $CCETD_HOME && \
  cd $CCETD_HOME && \
  mkdir instance && \
  git checkout -b development && \
  git pull origin development && \
  pip3 install -r requirements.txt
  
COPY $CCETD_CONF $CCETD_HOME/instance/conf.py
COPY workflows/library-science.ini $CCETD_HOME/workflows/library-science.ini

WORKDIR $CCETD_HOME
EXPOSE 8095

CMD ["python", "run.py"]
