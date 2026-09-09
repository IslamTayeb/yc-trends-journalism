"""Harness for streamlit.testing: renders one view (env VIEW) with the real sidebar. Not a user page."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib  # noqa: E402

import streamlit as st  # noqa: E402

import app  # noqa: E402

app.sidebar()
view = importlib.import_module(f"views.{os.environ['VIEW']}")
view.render()
