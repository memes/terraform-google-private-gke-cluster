FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm
# Temporary workaround for yarn GPG expiration
RUN curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | \
    sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/yarn-archive-keyring.gpg
