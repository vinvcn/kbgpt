FROM    centos:7

RUN     yum -y install vim git net-tools telnet wget gcc gcc-c++ unzip ncurses-devel sqlite-devel make \
    bzip2 bzip2-devel gdbm-devel readline-devel zlib-devel xz openssl-devel libffi libffi-devel && yum clean all && mkdir /home/app \
    && wget -q https://sg-share-file.oss-ap-southeast-1.aliyuncs.com/yunwei/k8sfile/pack/Python-3.8.13.tgz \
    && tar xf Python-3.8.13.tgz && cd Python-3.8.13 && ./configure --prefix=/usr/local/python && make && make install \
    && mv /usr/bin/python /usr/bin/python_old && sed -i 's;#!/usr/bin/python;#!/usr/bin/python2.7;' /usr/bin/yum \
    && sed -i 's;#! /usr/bin/python;#!/usr/bin/python2.7;' /usr/libexec/urlgrabber-ext-down \
    && ln -sf /usr/local/python/bin/python{3,}

ENV     PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin PYTHON_HOME=/usr/local/python
ENV     PATH=$PATH:$PYTHON_HOME/bin
RUN     python3.8 -m pip install --upgrade pip && pip3 install --upgrade setuptools

RUN     curl -sSL https://install.python-poetry.org | python3 -

RUN     export PATH=$PATH:$HOME/.local/bin

WORKDIR /app

COPY    . .

RUN     poetry install

CMD     ["poetry", "run", "python", "main.py", "server"]