FROM almalinux:8

# Install AlmaLinux platform Python and common development tools.
RUN dnf -y update \
    && dnf -y install \
        python3-pip \
        git \
        curl \
        sudo \
        zsh \
        which \
        ca-certificates \
        shadow-utils \
    && dnf clean all

# Install StGit from GitHub (the version in the repos is too old)
RUN set -eux; \
    arch="$(uname -m)"; \
    dnf -y install https://github.com/stacked-git/stgit/releases/download/v2.5.5/stgit-2.5.5-1.${arch}.rpm; \
    dnf clean all

# Create a non-root user for VS Code.
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m --shell /bin/zsh ${USERNAME} \
    && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

WORKDIR /workspaces/placement-client

USER ${USERNAME}
