#!/usr/bin/env python3
import sys
print("Python started", flush=True)

try:
    print("Importing json...", flush=True)
    import json
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAIL: {e}", flush=True)
    sys.exit(1)

try:
    print("Importing os...", flush=True)
    import os
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAIL: {e}", flush=True)
    sys.exit(1)

try:
    print("Importing pathlib...", flush=True)
    from pathlib import Path
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAIL: {e}", flush=True)
    sys.exit(1)

try:
    print("Importing dotenv...", flush=True)
    from dotenv import load_dotenv
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAIL: {e}", flush=True)
    sys.exit(1)

try:
    print("Importing google.genai...", flush=True)
    from google import genai
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAIL: {e}", flush=True)
    sys.exit(1)

try:
    print("Importing google.genai.types...", flush=True)
    from google.genai import types
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAIL: {e}", flush=True)
    sys.exit(1)

print("\nAll imports successful!", flush=True)