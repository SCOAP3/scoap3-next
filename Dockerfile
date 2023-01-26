FROM python:2.7.18

ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 6.17.1

RUN mkdir -p $NVM_DIR

# Install nvm with node and npm
RUN curl --silent -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash

# Install node and npm
RUN . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

# add node and npm to path so the commands are available
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
    pip install --no-cache-dir --upgrade wheel && \
    pip install --no-cache-dir typing==3.7.4.1

COPY . .

RUN pip install --ignore-installed --requirement requirements.txt && \
    pip install -e .

WORKDIR /usr/local/var/scoap3-instance/static

RUN scoap3 npm && \
    npm install && \
    scoap3 collect -v && \
    scoap3 assets build

WORKDIR /code
