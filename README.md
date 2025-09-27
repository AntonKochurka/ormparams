ORMParams
===========

[![PyPI](https://img.shields.io/pypi/v/ormparams)](https://pypi.org/project/ormparams)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/AntonKochurka/ormparams)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)



Query parameter parser and filter for ORM-based applications. Soon will include a FastAPI extension.


## Installation

```bash
pip install ormparams
````

Also, for the upcoming FastAPI integration:

```bash
pip install "ormparams[fastapi]"
```


## Quick Start

ORMParams provides four main components:

1. **SuffixSet** – defines the set of suffixes and their functionality for filtering and serialization of data.  [ [ > ] ](./docs/SuffixSet.md)
2. **ParserRules** – defines the set of rules for parsing, specifying how each input should be processed.  [ [ > ] ](./docs/ParserRules.md)
3. **Parser** – implements the logic of separating URL parameters into tokens according to a unified format.  
4. **OrmFilter** – applies filters to ORM queries based on standardized data.

Each of these logical components has its own documentation in [docs](./docs/). (not finalized)