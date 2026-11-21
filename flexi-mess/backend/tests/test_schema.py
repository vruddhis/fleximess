"""Read-only check that every ORM model matches the live Supabase schema."""
from sqlalchemy import inspect

from app.database import Base, engine
import app.models  # noqa: F401  (registers models)


def test_models_match_live_schema():
    insp = inspect(engine)
    live_tables = set(insp.get_table_names(schema="public"))
    problems = []
    for name, table in Base.metadata.tables.items():
        if name not in live_tables:
            problems.append(f"table {name} does not exist in Supabase")
            continue
        live = {c["name"]: c for c in insp.get_columns(name, schema="public")}
        for col in table.columns:
            if col.name not in live:
                problems.append(f"{name}.{col.name} does not exist in Supabase")
            elif live[col.name]["nullable"] != col.nullable and not col.primary_key:
                problems.append(f"{name}.{col.name} nullable mismatch: model={col.nullable} db={live[col.name]['nullable']}")
        # NOT NULL columns without a DB default must be mapped, or inserts would fail.
        mapped = {c.name for c in table.columns}
        for cname, c in live.items():
            if not c["nullable"] and c.get("default") is None and not c.get("identity") and cname not in mapped:
                problems.append(f"{name}.{cname} is NOT NULL without default but not mapped")
    assert not problems, "\n".join(problems)


def test_no_favorites_model():
    assert "favorites" not in Base.metadata.tables


def test_app_does_not_create_tables_on_startup():
    from app.main import app as fastapi_app
    assert not fastapi_app.router.on_startup, "Startup hooks must not run DDL against Supabase"
