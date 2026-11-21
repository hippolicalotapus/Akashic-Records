#!/usr/bin/env python3
"""Build the site from data/records/*.json."""
import json, pathlib, shutil, sys
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "records"
OUT = ROOT / "records"
SCHEMA = json.loads((ROOT / "schema" / "record.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
NAMES = json.loads((ROOT / "data" / "collections.json").read_text())
