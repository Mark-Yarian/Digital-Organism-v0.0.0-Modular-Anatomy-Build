from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

def short_hash(value: Any, length: int = 16) -> str:
    return stable_hash(value)[:length]

def hash_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode()).hexdigest()[:16]

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def safe_slug(value: str) -> str:
    s = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in s: s=s.replace("--","-")
    return s.strip("-") or "organism"

def read_json(path: Path, default: Any) -> Any:
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")

def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True, default=str) + "\\n")

def load_jsonl(path: Path, limit: Optional[int]=None) -> List[Dict[str, Any]]:
    if not path.exists(): return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if limit is not None: lines = lines[-limit:]
    out=[]
    for line in lines:
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def safe_path_value(value: str) -> str:
    try:
        home = str(Path.home())
        return value.replace(home, "~") if home else value
    except Exception:
        return value

def redact_text(text: str) -> str:
    if not text: return text
    redacted = text
    for pat in [
        r"(?i)(password\\s*[:=]\\s*)(\\S+)",
        r"(?i)(passwd\\s*[:=]\\s*)(\\S+)",
        r"(?i)(pwd\\s*[:=]\\s*)(\\S+)",
        r"(?i)(token\\s*[:=]\\s*)(\\S+)",
        r"(?i)(secret\\s*[:=]\\s*)(\\S+)",
        r"(?i)(api[_-]?key\\s*[:=]\\s*)(\\S+)",
        r"(?i)(authorization\\s*[:=]\\s*)(.+)",
        r"(?i)(bearer\\s+)([A-Za-z0-9._\\-]+)",
    ]:
        redacted = re.sub(pat, r"\\1[REDACTED]", redacted)
    return safe_path_value(redacted)
