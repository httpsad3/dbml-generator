#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect


def load_env(env: str) -> dict:
    env_file = Path(f".env.{env}")
    if not env_file.exists():
        print(f"Error: '{env_file}' not found. Create it from the .example file.")
        sys.exit(1)
    load_dotenv(env_file, override=True)
    return {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": os.getenv("DB_PORT", ""),
        "DB_USER": os.getenv("DB_USER", ""),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
        "DB_NAME": os.getenv("DB_NAME", ""),
        "DB_TYPE": os.getenv("DB_TYPE", "mysql").lower(),
        "OUTPUT_FILE": os.getenv("OUTPUT_FILE", f"schema_{env}.dbml"),
    }


def build_connection_url(config: dict) -> str:
    db_type = config["DB_TYPE"]
    host = config["DB_HOST"]
    port = config["DB_PORT"]
    user = config["DB_USER"]
    password = config["DB_PASSWORD"]
    name = config["DB_NAME"]

    if db_type == "sqlite":
        return f"sqlite:///{name}"

    drivers = {
        "mysql": "mysql+pymysql",
        "postgresql": "postgresql+psycopg2",
        "postgres": "postgresql+psycopg2",
    }
    driver = drivers.get(db_type, db_type)
    port_part = f":{port}" if port else ""
    return f"{driver}://{user}:{password}@{host}{port_part}/{name}"


def map_column_type(col_type) -> str:
    type_str = str(col_type).upper()
    base = type_str.split("(")[0].strip()

    simple_map = {
        "INTEGER": "int",
        "INT": "int",
        "BIGINT": "bigint",
        "SMALLINT": "smallint",
        "TINYINT": "tinyint",
        "MEDIUMINT": "int",
        "TEXT": "text",
        "LONGTEXT": "text",
        "MEDIUMTEXT": "text",
        "TINYTEXT": "text",
        "CLOB": "text",
        "BOOLEAN": "boolean",
        "BOOL": "boolean",
        "DATETIME": "datetime",
        "TIMESTAMP": "timestamp",
        "DATE": "date",
        "TIME": "time",
        "FLOAT": "float",
        "DOUBLE": "float",
        "DOUBLE PRECISION": "float",
        "REAL": "float",
        "BLOB": "blob",
        "BINARY": "blob",
        "VARBINARY": "blob",
        "LONGBLOB": "blob",
        "MEDIUMBLOB": "blob",
        "JSON": "json",
        "UUID": "uuid",
    }

    # Keep parameterized types intact (VARCHAR(255), CHAR(10), DECIMAL(10,2), etc.)
    if base in ("VARCHAR", "CHAR", "NVARCHAR", "CHARACTER VARYING"):
        return type_str.lower()
    if base in ("DECIMAL", "NUMERIC"):
        return type_str.lower()

    return simple_map.get(base, type_str.lower())


def format_default(raw_default) -> str | None:
    if raw_default is None:
        return None

    val = str(raw_default).strip()

    if val.upper() in ("NULL", "NONE", ""):
        return None

    # Pure number
    try:
        float(val)
        return val
    except ValueError:
        pass

    # Boolean literals
    if val.lower() in ("true", "false"):
        return val.lower()

    # Already a single-quoted string, keep as-is
    if val.startswith("'") and val.endswith("'") and len(val) >= 2:
        return val

    # Anything else (SQL expressions, functions) → backtick-wrap for DBML
    return f"`{val}`"


def generate_dbml(engine) -> tuple[str, int, int, int]:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    blocks: list[str] = []
    refs: list[str] = []
    total_columns = 0

    for table in table_names:
        columns = inspector.get_columns(table)
        pk_info = inspector.get_pk_constraint(table)
        pk_cols = set(pk_info.get("constrained_columns", []))
        fk_list = inspector.get_foreign_keys(table)

        lines = [f"Table {table} {{"]

        for col in columns:
            name = col["name"]
            col_type = map_column_type(col["type"])
            nullable = col.get("nullable", True)
            autoincrement = col.get("autoincrement", False)
            raw_default = col.get("default")

            attrs: list[str] = []

            if name in pk_cols:
                attrs.append("pk")
                if autoincrement:
                    attrs.append("increment")
            elif not nullable:
                attrs.append("not null")

            default_str = format_default(raw_default)
            if default_str is not None:
                attrs.append(f"default: {default_str}")

            note = col.get("comment")
            if note:
                safe_note = note.replace("'", "\\'")
                attrs.append(f"note: '{safe_note}'")

            attr_part = f" [{', '.join(attrs)}]" if attrs else ""
            lines.append(f"  {name} {col_type}{attr_part}")
            total_columns += 1

        lines.append("}")
        blocks.append("\n".join(lines))

        for fk in fk_list:
            for local_col, ref_col in zip(
                fk["constrained_columns"], fk["referred_columns"]
            ):
                refs.append(
                    f"Ref: {table}.{local_col} > {fk['referred_table']}.{ref_col}"
                )

    output_parts = ["\n\n".join(blocks)]

    if refs:
        output_parts.append("\n".join(refs))

    return "\n\n".join(output_parts) + "\n", len(table_names), total_columns, len(refs)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a .dbml schema file from a relational database."
    )
    parser.add_argument(
        "--env",
        required=True,
        metavar="ENV",
        help="Environment name (e.g. local, prod). Loads .env.<ENV>",
    )
    args = parser.parse_args()

    env = args.env
    config = load_env(env)

    db_type = config["DB_TYPE"]
    db_name = config["DB_NAME"]
    output_file = config["OUTPUT_FILE"]

    print(f"[dbml-generator] Environment : {env}")
    print(f"[dbml-generator] Database    : {db_type}://{db_name}")
    print(f"[dbml-generator] Connecting...")

    try:
        url = build_connection_url(config)
        engine = create_engine(url)
        with engine.connect():
            pass
    except Exception as exc:
        print(f"\nError: could not connect to database.\n  {exc}")
        sys.exit(1)

    print("[dbml-generator] Inspecting schema...")

    try:
        dbml_content, table_count, col_count, ref_count = generate_dbml(engine)
    except Exception as exc:
        print(f"\nError while inspecting schema:\n  {exc}")
        sys.exit(1)

    Path(output_file).write_text(dbml_content, encoding="utf-8")

    print()
    print("=" * 40)
    print("  Summary")
    print("=" * 40)
    print(f"  Environment  : {env}")
    print(f"  Tables       : {table_count}")
    print(f"  Columns      : {col_count}")
    print(f"  References   : {ref_count}")
    print(f"  Output file  : {output_file}")
    print("=" * 40)
    print()
    print(f"Done! Paste the contents of '{output_file}' into https://dbdiagram.io")


if __name__ == "__main__":
    main()
