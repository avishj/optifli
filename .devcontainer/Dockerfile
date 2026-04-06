# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# v0.11.3
FROM ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 AS uv

# 3.13
FROM mcr.microsoft.com/devcontainers/python:3.13@sha256:9b0762901a555c31c2c63824cb5b1ade77da939500e034317b8d09578b94ba0e

COPY --from=uv /uv /uvx /usr/local/bin/

RUN UV_TOOL_BIN_DIR=/usr/local/bin uv tool install just==1.48.1
