"""Lightweight logging so agent activity can be inspected outside Streamlit too."""
import logging
import sys

logger = logging.getLogger("ai_data_analyst")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
