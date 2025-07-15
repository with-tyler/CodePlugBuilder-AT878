# utils.py
import sys

def error(message):
    print(f"ERROR: {message}")
    sys.exit(1)

def warning(message):
    print(f"WARNING: {message}")