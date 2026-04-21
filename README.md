<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# optifli

[![CI](https://github.com/avishj/optifli/actions/workflows/ci.yml/badge.svg)](https://github.com/avishj/optifli/actions/workflows/ci.yml)
[![CodeQL](https://github.com/avishj/optifli/actions/workflows/_codeql.yml/badge.svg)](https://github.com/avishj/optifli/actions/workflows/_codeql.yml)
[![codecov](https://codecov.io/gh/avishj/optifli/branch/main/graph/badge.svg)](https://codecov.io/gh/avishj/optifli)
[![PyPI](https://img.shields.io/pypi/v/optifli)](https://pypi.org/project/optifli/)
[![Downloads](https://img.shields.io/pypi/dm/optifli)](https://pypi.org/project/optifli/)
[![Python](https://img.shields.io/pypi/pyversions/optifli)](https://pypi.org/project/optifli/)
[![License](https://img.shields.io/github/license/avishj/optifli)](LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/avishj/optifli/badge)](https://scorecard.dev/viewer/?uri=github.com/avishj/optifli)
[![Docker Hub](https://img.shields.io/docker/v/avishj/optifli?label=docker%20hub)](https://hub.docker.com/r/avishj/optifli)
[![GHCR](https://ghcr-badge.egpl.dev/avishj/optifli/latest_tag?label=ghcr)](https://github.com/avishj/optifli/pkgs/container/optifli)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=avishj_optifli&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=avishj_optifli)

CLI-first flight optimization engine for multi-city itineraries.

## Features

- Subcommand-based CLI built with [Cyclopts](https://cyclopts.readthedocs.io/)
- Rich terminal output via [Rich](https://rich.readthedocs.io/)
- Typed configuration from environment variables and `.env` files via [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- Fully typed with [PEP 561](https://peps.python.org/pep-0561/) `py.typed` marker
- Python 3.13+ support

## Installation

```bash
uv tool install optifli
```

Or with pip:

```bash
pip install optifli
```

Or with Docker:

```bash
docker run --rm ghcr.io/avishj/optifli --help
# or
docker run --rm docker.io/avishj/optifli --help
```

## Usage

```bash
optifli --help
optifli optimize --help
```

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

### Setup

```bash
git clone https://github.com/avishj/optifli.git
cd optifli
uv sync
pre-commit install
```

### Common tasks

```bash
just lint    # run all pre-commit hooks (ruff, ty, complexipy, reuse, etc.)
just test    # run all tests with coverage
just build   # build sdist + wheel, twine check, entry point smoke test
just docs    # build and serve docs locally
just ci      # full composite gate (lint + test + build + docs)
just clean   # remove build artifacts
```

## Configuration

optifli reads configuration from environment variables prefixed with `OPTIFLI_` and from `.env` files.

| Variable | Default | Description |
| --- | --- | --- |
| `OPTIFLI_VERBOSE` | `false` | Enable verbose output |
| `OPTIFLI_LOG_FORMAT` | `pretty` | Logger output format: `pretty` or `json` |

## Documentation

[https://avishj.github.io/optifli](https://avishj.github.io/optifli)

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes and run `just ci` to verify
4. Commit using [conventional commits](https://www.conventionalcommits.org/)
5. Open a pull request

## License

[AGPL-3.0-or-later](LICENSE)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=avishj/optifli&type=Date)](https://star-history.com/#avishj/optifli&Date)
