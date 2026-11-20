import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api.main import app

target = Path(__file__).resolve().parents[1] / "docs/openapi-v2.json"
spec = app.openapi()
target.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Contrato v2 exportado: {sum(len(x) for x in spec['paths'].values())} operações e {len(spec['components']['schemas'])} schemas.")
