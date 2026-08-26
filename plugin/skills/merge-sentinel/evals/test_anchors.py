import sys, unittest
from pathlib import Path
SCRIPTS_DIR=Path(__file__).resolve().parents[1]/"scripts"; sys.path.insert(0,str(SCRIPTS_DIR))
from reviewlib.anchors import AnchorStatus, context_hash, normalize_context, resolve_anchor
from reviewlib.models import ValidationError
A="a"*40; B="b"*40; C="c"*40; L=["def calculate():","    value = 1","    return value"]
def request(**overrides):
 d={"schema_version":1,"prior":{"path":"src/service.py","blob_sha":A,"old_line":42,"qualified_symbol":"","context_lines":L},"provider":{"new_path":"src/service.py","new_blob_sha":B,"new_line":45,"renamed":False},"target_candidates":[{"path":"src/service.py","blob_sha":B,"line":45,"qualified_symbol":"","context_lines":L,"provenance":"provider"}]}
 d.update(overrides); return d
class AnchorTests(unittest.TestCase):
 def test_provider_position_exact(self):
  x=resolve_anchor(request()); self.assertEqual(x["status"],"exact"); self.assertEqual(x["method"],"provider-position"); self.assertIsNotNone(x["selected"])
 def test_provider_rename_moved(self):
  x=resolve_anchor(request(provider={"new_path":"src/new.py","new_blob_sha":"","new_line":0,"renamed":True},target_candidates=[{"path":"src/new.py","blob_sha":C,"line":9,"qualified_symbol":"","context_lines":L,"provenance":"provider"}])); self.assertEqual((x["status"],x["method"]),("moved","provider-rename"))
 def test_unique_context_move(self):
  x=resolve_anchor(request(provider={"new_path":"","new_blob_sha":"","new_line":0,"renamed":False},target_candidates=[{"path":"src/new.py","blob_sha":C,"line":9,"qualified_symbol":"","context_lines":L,"provenance":"repository"}])); self.assertEqual((x["status"],x["method"]),("moved","context-hash"))
 def test_duplicate_context_ambiguous(self):
  cs=[{"path":p,"blob_sha":C,"line":9,"qualified_symbol":"","context_lines":L,"provenance":"repository"} for p in ("src/a.py","src/b.py")]; x=resolve_anchor(request(provider={"new_path":"","new_blob_sha":"","new_line":0,"renamed":False},target_candidates=cs)); self.assertEqual(x["status"],"ambiguous"); self.assertIsNone(x["selected"]); self.assertEqual(len(x["candidates"]),2)
 def test_deleted_context_missing(self):
  x=resolve_anchor(request(provider={"new_path":"","new_blob_sha":"","new_line":0,"renamed":False},target_candidates=[])); self.assertEqual(x["status"],"missing")
 def test_context_requires_three_lines(self):
  with self.assertRaises(ValidationError): normalize_context(["a","b"])
 def test_context_normalization_is_stable(self): self.assertEqual(context_hash(L),context_hash(["\r\ndef calculate():  ","  value = 1\r","return value\n"]))
