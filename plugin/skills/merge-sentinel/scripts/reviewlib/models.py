from __future__ import annotations
import json, math, os, re
from pathlib import Path, PurePosixPath
SCHEMA_VERSION=1; CONTROLLER_VERSION=SKILL_VERSION="0.1.0"; MAX_INPUT_BYTES=5_000_000; MAX_PACKET_BYTES=250_000; MAX_STRING_CHARS=20_000; MAX_LIST_ITEMS=5_000; MAX_JSON_DEPTH=20; MAX_EXPANSION_LEASES=2; GIT_TIMEOUT_SECONDS=15; MERGEABILITY_ATTEMPTS=4; MERGEABILITY_INTERVAL_SECONDS=2; FINGERPRINT_HEX_CHARS=24
class ValidationError(ValueError): pass
class IncompatibleSchemaError(ValidationError): pass
def _pairs(pairs):
 d={}
 for k,v in pairs:
  if k in d: raise ValidationError(f"duplicate key: {k}")
  d[k]=v
 return d
def validate_json_value(value,*,depth=0):
 if depth>MAX_JSON_DEPTH: raise ValidationError("JSON nesting too deep")
 if isinstance(value,float) and not math.isfinite(value): raise ValidationError("non-finite number")
 if isinstance(value,str) and len(value)>MAX_STRING_CHARS: raise ValidationError("string too long")
 if isinstance(value,list):
  if len(value)>MAX_LIST_ITEMS: raise ValidationError("list too long")
  for x in value: validate_json_value(x,depth=depth+1)
 if isinstance(value,dict):
  for k,v in value.items():
   if not isinstance(k,str): raise ValidationError("non-string object key")
   validate_json_value(v,depth=depth+1)
def load_json(path:Path,*,max_bytes=MAX_INPUT_BYTES):
 if path.stat().st_size>max_bytes: raise ValidationError("input too large")
 try: value=json.loads(path.read_bytes().decode("utf-8"),object_pairs_hook=_pairs)
 except (OSError,UnicodeDecodeError,json.JSONDecodeError) as e: raise ValidationError(str(e)) from e
 if not isinstance(value,dict): raise ValidationError("top-level object required")
 validate_json_value(value); return value
def canonical_json_bytes(value):
 validate_json_value(value); return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def atomic_write_json(path:Path,value):
 temp=path.with_name(f"{path.name}.tmp.{os.getpid()}")
 try:
  with open(temp,"wb") as f: f.write(canonical_json_bytes(value)); f.flush(); os.fsync(f.fileno())
  os.replace(temp,path)
 except Exception:
  try: temp.unlink()
  except FileNotFoundError: pass
  raise
def normalize_repo_path(value):
 if not isinstance(value,str): raise ValidationError("path must be string")
 value=value.replace("\\","/")
 if not value or "\0" in value or value.startswith("/") or value.startswith("//") or re.match(r"^[A-Za-z]:",value): raise ValidationError("unsafe repository path")
 if any(x in ("", ".", "..") for x in value.split("/")): raise ValidationError("unsafe repository path")
 return str(PurePosixPath(value))
def require_schema(document):
 if document.get("schema_version")!=1: raise IncompatibleSchemaError(f"unsupported schema_version: {document.get('schema_version')}; supported: 1")
