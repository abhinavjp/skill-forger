import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SCRIPTS_DIR=Path(__file__).resolve().parents[1]/"scripts"; sys.path.insert(0,str(SCRIPTS_DIR))
from reviewlib.fingerprints import finding_fingerprint, normalize_finding
from reviewlib.queue import QueueError, complete_lease, new_queue, request_lease
from reviewlib.rereview import build_packet
from reviewlib.models import ValidationError

VALIDATOR = SCRIPTS_DIR / "validate_publication.py"

def publication_input(**overrides):
 data = {
  "schema_version": 1, "operation_id": "op-1", "operation": "top-level-note",
  "authority": "top-level-note", "snapshot": {"head_sha": "a" * 40, "diff_version": "1"},
  "remote": {"head_sha": "a" * 40, "diff_version": "1", "mergeability": "mergeable"},
  "position": {"base_sha": "", "start_sha": "", "head_sha": "", "path": "", "new_line": 0, "commentable": False},
  "idempotency_key": "key-1",
 }
 data.update(overrides)
 return data

def run_publication(data, ledger=None):
 with tempfile.TemporaryDirectory() as temp:
  root = Path(temp); input_path = root / "input.json"; ledger_path = root / "ledger.json"
  input_path.write_text(json.dumps(data), encoding="utf-8")
  if ledger is not None: ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
  result = subprocess.run([sys.executable, str(VALIDATOR), "validate", "--input", str(input_path), "--ledger", str(ledger_path)], capture_output=True, text=True)
  return result, json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else None
class ReviewStateTests(unittest.TestCase):
 def test_fingerprint_stable_for_whitespace_and_path_separator(self): self.assertEqual(finding_fingerprint("a\\b.py"," A  B ","x"),finding_fingerprint("a/b.py","a b","x"))
 def test_caller_fingerprint_rejected(self):
  with self.assertRaises(ValidationError): normalize_finding({"fingerprint":"x"})
 def test_queue_happy_path(self):
  q=new_queue("s"); q=request_lease(q,"i","e"); q=complete_lease(q,next(iter(q["leases"])),"proven","a"*64); self.assertEqual((q["entries"][next(iter(q["entries"]))]["state"],q["revision"]),("proven",2))
 def test_queue_rejects_third_lease(self):
  q=new_queue("s")
  for _ in range(2): q=request_lease(q,"i","e"); q=complete_lease(q,next(k for k,v in q["leases"].items() if not v["completed"]),"unresolved",None)
  with self.assertRaises(QueueError): request_lease(q,"i","e")
 def test_packet_exact_allows_actions(self): self.assertTrue(build_packet({"fingerprint":"a"*24},{"status":"exact","selected":{}},{"head_sha":"a"*40})["automatic_actions_allowed"])
 def test_packet_ambiguous_forbids_actions(self): self.assertFalse(build_packet({"fingerprint":"a"*24},{"status":"ambiguous"},{"head_sha":"a"*40})["automatic_actions_allowed"])

 def test_read_only_cannot_publish(self):
  result, _ = run_publication(publication_input(authority="read-only")); self.assertEqual(result.returncode, 2)
 def test_authority_must_match_operation(self):
  result, _ = run_publication(publication_input(authority="reply")); self.assertEqual(result.returncode, 2)
 def test_stale_head_rejected(self):
  result, _ = run_publication(publication_input(remote={"head_sha":"b"*40,"diff_version":"1","mergeability":"mergeable"})); self.assertEqual(result.returncode, 2)
 def test_stale_diff_version_rejected(self):
  result, _ = run_publication(publication_input(remote={"head_sha":"a"*40,"diff_version":"2","mergeability":"mergeable"})); self.assertEqual(result.returncode, 2)
 def test_inline_requires_commentable_position(self):
  result, _ = run_publication(publication_input(operation="inline-discussion",authority="inline-discussion")); self.assertEqual(result.returncode, 2)
 def test_confirmed_operation_is_idempotent(self):
  ledger={"schema_version":1,"revision":1,"operations":{"key-1":{"operation_id":"op-1","idempotency_key":"key-1","state":"confirmed","remote_object_id":"remote-1","last_error":""}}}
  result, written = run_publication(publication_input(), ledger); self.assertEqual(result.returncode, 0); self.assertEqual(json.loads(result.stdout)["next_action"], "skip"); self.assertEqual(written["revision"], 1)
 def test_uncertain_requires_verification(self):
  ledger={"schema_version":1,"revision":1,"operations":{"key-1":{"operation_id":"op-1","idempotency_key":"key-1","state":"uncertain","remote_object_id":"","last_error":"timeout"}}}
  result, _ = run_publication(publication_input(), ledger); self.assertEqual(result.returncode, 2)
 def test_approval_requires_mergeable(self):
  for mergeability in ("blocked", "indeterminate"):
   result, _ = run_publication(publication_input(operation="approve",authority="approve",remote={"head_sha":"a"*40,"diff_version":"1","mergeability":mergeability})); self.assertEqual(result.returncode, 2)
 def test_partial_write_resume_skips_confirmed(self):
  ledger={"schema_version":1,"revision":1,"operations":{"done":{"operation_id":"done","idempotency_key":"done","state":"confirmed","remote_object_id":"remote-1","last_error":""}}}
  result, written = run_publication(publication_input(operation_id="next",idempotency_key="next"), ledger); self.assertEqual(result.returncode, 0); self.assertEqual(json.loads(result.stdout)["next_action"], "attempt"); self.assertEqual(written["operations"]["next"]["state"], "intended")

 def test_lock_contention_exits_four(self):
  with tempfile.TemporaryDirectory() as temp:
   state = Path(temp) / "queue.json"; state.write_text(json.dumps(new_queue("snapshot")), encoding="utf-8")
   lock = state.with_name(state.name + ".lock"); lock.write_text("", encoding="utf-8")
   result = subprocess.run([sys.executable, str(SCRIPTS_DIR / "review_state.py"), "request-lease", "--state", str(state), "--invariant-id", "invariant", "--evidence-key", "evidence"], capture_output=True, text=True)
  self.assertEqual(result.returncode, 4); self.assertEqual(result.stderr, "state is locked\n")

 def test_new_queue_writes_and_prints_canonical_json(self):
  with tempfile.TemporaryDirectory() as temp:
   state = Path(temp) / "queue.json"
   result = subprocess.run([sys.executable, str(SCRIPTS_DIR / "review_state.py"), "new-queue", "--snapshot-id", "snapshot", "--output", str(state)], capture_output=True, text=True)
   self.assertEqual(result.returncode, 0)
   self.assertEqual(result.stdout, state.read_text(encoding="utf-8") + "\n")
   self.assertEqual(json.loads(result.stdout), new_queue("snapshot"))
