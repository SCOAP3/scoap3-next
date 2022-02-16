FROM python:2.7.18


# Install base dependencies
RUN apt-get update && apt-get install -y -q --no-install-recommends

RUN apt-get install -y  imagemagick wget

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

ENV NODE_VERSION 6.17.1
RUN mkdir /usr/local/nvm
ENV NVM_DIR /usr/local/nvm

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash

# install node and npm LTS
RUN source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

RUN npm install -g \
    node-sass@3.8.0 \
    clean-css@^3.4.24 \
    requirejs \
    uglify-js

WORKDIR /code

RUN pip install --no-cache-dir --upgrade pip==20.3.4 && \
    pip install --no-cache-dir --upgrade setuptools && \
    pip install --no-cache-dir --upgrade wheel

COPY . .

RUN pip install --ignore-installed --requirement requirements.txt && \
    pip install -e .

WORKDIR /usr/local/var/scoap3-instance/static

RUN scoap3 npm && \
    npm install && \
    scoap3 collect -v && \
    scoap3 assets build

WORKDIR /code
