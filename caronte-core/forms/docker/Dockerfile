FROM ubuntu:20.04 AS base-env

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y -qq && apt-get install -y -qq --no-install-recommends \
    ca-certificates \
    locales \
    python3.9 \
    python3.9-venv \
    postgresql \
    libmagic1 libmagic-dev && \
    #
    localedef -i pt_BR -c -f UTF-8 -A /usr/share/locale/locale.alias pt_BR.UTF-8 && \
    update-ca-certificates && \
    apt-get -y autoclean && apt-get -y autoremove && apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=pt_BR.utf8

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
RUN update-alternatives --set python3 /usr/bin/python3.9

# install pip requirements libraries
FROM base-env AS build-env

RUN apt-get update -y -qq && apt-get install -y -qq --no-install-recommends \
    python3.9-dev \
    build-essential \
    git \
    libpq-dev && \
    #
    localedef -i pt_BR -c -f UTF-8 -A /usr/share/locale/locale.alias pt_BR.UTF-8 && \
    update-ca-certificates && \
    apt-get -y autoclean && apt-get -y autoremove && apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base-env AS final-env

COPY --from=build-env /opt/venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 5000

COPY . /src

WORKDIR /src
RUN pybabel compile -d translations

RUN groupadd -g 1001 appgroup \
    && useradd -m -u 1001 -g appgroup -s /bin/bash appuser

RUN chown -R appuser:appgroup /src
RUN mkdir -p /src/tmp && chown -R appuser:appgroup /src/tmp
RUN mkdir -p /src/logs && chown -R appuser:appgroup /src/logs
RUN mkdir -p /shared/tmp && chown -R appuser:appgroup /shared/tmp
RUN mkdir -p /shared/uploads && chown -R appuser:appgroup /shared/uploads

USER appuser