FROM mcr.microsoft.com/devcontainers/python:1-3.9-bullseye

# Prevents Python from writing pyc files and enables unbuffered logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mv -f /etc/apt/sources.list.d/yarn.list{,.bak} || :
# ^^ GPG key is broken

# Install stacked git
ARG STGIT_VERSION=2.5.5
RUN ARCH=$(dpkg --print-architecture) && \
    wget https://github.com/stacked-git/stgit/releases/download/v${STGIT_VERSION}/stgit_${STGIT_VERSION}-1_${ARCH}.deb && \
    apt install ./stgit_${STGIT_VERSION}-1_${ARCH}.deb && \
    rm -f ./stgit_${STGIT_VERSION}-1_${ARCH}.deb

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/uv
ENV UV_LINK_MODE=copy

RUN mkdir -p /etc/condor
RUN touch /etc/condor/condor_config  # create a dummy config to silence a warning from htcondor2
