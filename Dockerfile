# Dockerfile for CCETD
FROM tuttlibrary/python-base
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV CCETD_HOME /opt/ccetd/

RUN mkdir $CCETD_HOME && \
    mkdir $CCETD_HOME/instance && \
    mkdir $CCETD_HOME/custom

COPY etd/ $CCETD_HOME/etd
COPY instance/ $CCETD_HOME/instance
COPY custom/ $CCETD_HOME/custom
COPY VERSION $CCETD_HOME/.
COPY run.py $CCETD_HOME/.

RUN cd $CCETD_HOME && \
    git clone https://github.com/Tutt-Library/fedora38-utilities.git && \
    cd fedora38-utilities && python3 setup.py install

EXPOSE 8084
WORKDIR $CCETD_HOME

CMD ["nohup", "gunicorn", "-w 2", "-b :8084", "-t 300", "run:parent_app", "&"]
