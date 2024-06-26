FROM python:3.8.6-buster
USER root

ARG VCS_REF="missing"
ARG BUILD_DATE="missing"

ENV VCS_REF=${VCS_REF}
ENV BUILD_DATE=${BUILD_DATE}

LABEL org.label-schema.vcs-ref=${VCS_REF} \
    org.label-schema.build-date=${BUILD_DATE}

USER root

# Installing Oracle instant client
WORKDIR    /opt/oracle
RUN        apt-get update && apt-get install -y libaio1 wget unzip \
    # && wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip \
    # && wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-sqlplus-linuxx64.zip \
    # && unzip instantclient-basiclite-linuxx64.zip \
    # && rm -f instantclient-basiclite-linuxx64.zip \
    # && unzip instantclient-sqlplus-linuxx64.zip \
    # && rm -f instantclient-sqlplus-linuxx64.zip \
    && wget https://download.oracle.com/otn_software/linux/instantclient/211000/instantclient-basiclite-linux.x64-21.1.0.0.0.zip \
    && wget https://download.oracle.com/otn_software/linux/instantclient/211000/instantclient-sqlplus-linux.x64-21.1.0.0.0.zip \
    && unzip instantclient-basiclite-linux.x64-21.1.0.0.0.zip \
    && rm -f instantclient-basiclite-linux.x64-21.1.0.0.0.zip \
    && unzip instantclient-sqlplus-linux.x64-21.1.0.0.0.zip \
    && rm -f instantclient-sqlplus-linux.x64-21.1.0.0.0.zip \
    && cd /opt/oracle/instantclient* \
    && rm -f *jdbc* *occi* *mysql* *README *jar uidrvci genezi adrci \
    && echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

# Create working directory
RUN mkdir /opt/app-root && chmod 755 /opt/app-root
WORKDIR /opt/app-root

# Install the requirements
COPY ./requirements.txt .

#RUN pip install --upgrade pip
RUN pip install pip==20.1.1
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TZ=PST8PDT
WORKDIR /
COPY ./crontab .
ARG SOURCE_REPO=webdevops
ARG GOCROND_VERSION=23.2.0
ADD https://github.com/$SOURCE_REPO/go-crond/releases/download/$GOCROND_VERSION/go-crond.linux.amd64 /usr/bin/go-crond
USER root
RUN chmod +x /usr/bin/go-crond
RUN echo $TZ > /etc/timezone

USER 1001

# Set Python path
ENV PYTHONPATH=/opt/app-root

EXPOSE 8080

ENTRYPOINT ["go-crond", "crontab", "--allow-unprivileged", "--verbose", "--log.json"]
