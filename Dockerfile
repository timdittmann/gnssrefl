FROM python:3.8-slim-buster 
LABEL maintainer="EARTHSCOPE"
ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH

# build requirements
RUN apt-get update && \
    apt-get install -y gfortran python3-pip unzip wget vim 

## executables
RUN mkdir -p /etc/gnssrefl/exe /etc/gnssrefl/orbits /etc/gnssrefl/refl_code/Files
COPY --chown=${NB_UID}:${NB_GID} vendor/gfzrnx_2.0-8219_armlx64 /etc/gnssrefl/exe/
COPY --chown=${NB_UID}:${NB_GID} vendor/gfzrnx_2.0-8219_lx64 /etc/gnssrefl/exe/

RUN if [ "$TARGETARCH" = "arm64" ] ; then \
  cp /etc/gnssrefl/exe/gfzrnx_2.0-8219_armlx64 /etc/gnssrefl/exe/gfzrnx; else \
  cp /etc/gnssrefl/exe/gfzrnx_2.0-8219_lx64 /etc/gnssrefl/exe/gfzrnx; \
  fi

RUN chmod +x /etc/gnssrefl/exe/gfzrnx

RUN cd /tmp && \
    wget https://terras.gsi.go.jp/ja/crx2rnx/RNXCMP_4.1.0_src.tar.gz \
    && tar -xf RNXCMP_4.1.0_src.tar.gz \
    && gcc -ansi -O2 RNXCMP_4.1.0_src/source/crx2rnx.c -o CRX2RNX \
    && cp CRX2RNX /etc/gnssrefl/exe/ \
    && rm -rf RNXCMP*

ENV PATH="/etc/gnssrefl/exe:$PATH" 

RUN pip install numpy --upgrade --ignore-installed
COPY --chown=${NB_UID}:${NB_GID} pyproject.toml README.md setup.py /usr/src/gnssrefl/
COPY --chown=${NB_UID}:${NB_GID} gnssrefl /usr/src/gnssrefl/gnssrefl
#RUN pip3 install --no-cache-dir /usr/src/gnssrefl
RUN pip3 install jupyterlab

ENV PYTHONPATH /usr/src/gnssrefl
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

ENV EXE=/etc/gnssrefl/exe
ENV ORBITS=/etc/gnssrefl/orbits
ENV REFL_CODE=/etc/gnssrefl/refl_code

RUN mkdir -p /etc/gnssrefl/refl_code/input/
RUN mv /usr/src/gnssrefl/gnssrefl/gpt_1wA.pickle /etc/gnssrefl/refl_code/input/
RUN mv /usr/src/gnssrefl/gnssrefl/station_pos.db /etc/gnssrefl/refl_code/Files/

WORKDIR /usr/src/gnssrefl

# Jupyter setup
COPY --chown=${NB_UID}:${NB_GID} scripts/jupyter_notebook_config.py /usr/src/gnssrefl/.jupyter/
EXPOSE 8888
