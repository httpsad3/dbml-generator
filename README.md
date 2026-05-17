# dbml-generator

Connects to any relational database supported by SQLAlchemy (MySQL, PostgreSQL, SQLite) and auto-generates a `.dbml` file ready to paste into [dbdiagram.io](https://dbdiagram.io).

---

## Requirements

- Python 3.10+
- Access to a running database

---

## Installation

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd dbml-generator
```

### 2. Create and activate a virtual environment

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

> **Ubuntu / Debian users:** if you get `ensurepip is not available`, install the `python3-venv` package first:
> ```bash
> sudo apt install python3-venv
> ```
> Then re-run the commands above.

**Windows (PowerShell)**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Each environment needs its own `.env` file. Start from the provided examples:

```bash
cp .env.local.example .env.local
cp .env.prod.example  .env.prod
```

Then edit the values in each file.

### Available variables

| Variable      | Required | Default               | Description                                      |
|---------------|----------|-----------------------|--------------------------------------------------|
| `DB_HOST`     | Yes*     | `localhost`           | Database host. Ignored for SQLite.               |
| `DB_PORT`     | No       | Driver default        | Database port. Ignored for SQLite.               |
| `DB_USER`     | Yes*     | —                     | Database user. Ignored for SQLite.               |
| `DB_PASSWORD` | Yes*     | —                     | Database password. Ignored for SQLite.           |
| `DB_NAME`     | Yes      | —                     | Database name (or file path for SQLite).         |
| `DB_TYPE`     | Yes      | `mysql`               | One of: `mysql`, `postgresql`, `sqlite`.         |
| `OUTPUT_FILE` | No       | `schema_{env}.dbml`   | Path/name of the generated file.                 |

*Not required for SQLite.

---

> **WARNING:** Never commit `.env.local` or `.env.prod` to version control.
> These files contain credentials. They are already excluded by `.gitignore`,
> but be extra careful when using `git add .` — always review what you stage.

---

## Usage

### Generate schema for local environment

```bash
python generate_dbml.py --env local
```

### Generate schema for production environment

```bash
python generate_dbml.py --env prod
```

### Use a custom environment name

Any `--env <name>` value is valid as long as a corresponding `.env.<name>` file exists:

```bash
cp .env.local.example .env.staging
# edit .env.staging ...
python generate_dbml.py --env staging
```

### Expected output

```
[dbml-generator] Environment : local
[dbml-generator] Database    : mysql://myapp_dev
[dbml-generator] Connecting...
[dbml-generator] Inspecting schema...

========================================
  Summary
========================================
  Environment  : local
  Tables       : 12
  Columns      : 87
  References   : 10
  Output file  : schema_local.dbml
========================================

Done! Paste the contents of 'schema_local.dbml' into https://dbdiagram.io
```

---

## Viewing the result in dbdiagram.io

1. Open [https://dbdiagram.io](https://dbdiagram.io) and click **Create your diagram**.
2. Clear the sample code in the left panel.
3. Open the generated `.dbml` file and copy its full contents.
4. Paste into the left panel — the diagram renders instantly on the right.
5. Use **Export → PNG / PDF / SQL** to share or document your schema.

---

## Deactivating the virtual environment

When you are done, deactivate the venv with:

```bash
deactivate
```

---

## Project structure

```
dbml-generator/
├── generate_dbml.py       # Main script
├── requirements.txt       # Python dependencies
├── .env.local.example     # Template for local environment
├── .env.prod.example      # Template for production environment
├── .gitignore
└── README.md
```
