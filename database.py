import json
import secrets
from datetime import datetime
from pathlib import Path
from dataclasses import asdict, is_dataclass

DB_FILE = Path("tax_database.json")


def load_database():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_database(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def generate_tax_id(year: int | None = None) -> str:
    if year is None:
        year = datetime.now().year

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    part1 = "".join(secrets.choice(alphabet) for _ in range(4))
    part2 = "".join(secrets.choice(alphabet) for _ in range(4))

    return f"TX-{year}-{part1}-{part2}"


def _to_dict(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not serializable")


def store_tax_return(inputs, result, profile=None):
    db = load_database()

    tax_id = generate_tax_id()
    while tax_id in db:
        tax_id = generate_tax_id()

    db[tax_id] = {
        "name": inputs.name,
        "province": inputs.province,
        "profile": profile or {},
        "inputs": _to_dict(inputs),
        "results": _to_dict(result),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    save_database(db)
    return tax_id


def retrieve_tax_return(tax_id: str):
    db = load_database()
    return db.get(tax_id)
