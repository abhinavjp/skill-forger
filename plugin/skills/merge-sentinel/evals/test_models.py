import os, sys, tempfile, unittest
from pathlib import Path
SCRIPTS_DIR=Path(__file__).resolve().parents[1]/"scripts"; sys.path.insert(0,str(SCRIPTS_DIR))
from reviewlib.models import ValidationError, IncompatibleSchemaError, atomic_write_json, load_json, normalize_repo_path, require_schema

class ModelTests(unittest.TestCase):
 def test_duplicate_json_keys_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json"; p.write_text('{"a":1,"a":2}')
   with self.assertRaises(ValidationError): load_json(p)
 def test_future_schema_rejected(self):
  with self.assertRaises(IncompatibleSchemaError): require_schema({"schema_version":2})
 def test_absolute_windows_and_posix_paths_rejected(self):
  for value in ("C:\\x","/x"):
   with self.assertRaises(ValidationError): normalize_repo_path(value)
 def test_atomic_write_preserves_original_on_replace_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json"; p.write_bytes(b"old")
   old=os.replace; os.replace=lambda *_: (_ for _ in ()).throw(OSError("no"))
   try:
    with self.assertRaises(OSError): atomic_write_json(p,{"a":1})
   finally: os.replace=old
   self.assertEqual(p.read_bytes(),b"old"); self.assertEqual(list(Path(d).glob("*.tmp.*")),[])
