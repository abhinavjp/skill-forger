import hashlib, unicodedata
from .models import ValidationError, FINGERPRINT_HEX_CHARS, normalize_repo_path
def normalize_invariant(value):
 value=" ".join(unicodedata.normalize("NFKC",value).strip().lower().split())
 if not value: raise ValidationError("empty invariant")
 return value
def finding_fingerprint(path,invariant,anchor_identity): return hashlib.sha256("\0".join(["v1",normalize_repo_path(path).casefold(),normalize_invariant(invariant),anchor_identity]).encode()).hexdigest()[:FINGERPRINT_HEX_CHARS]
def normalize_finding(candidate):
 if "fingerprint" in candidate: raise ValidationError("caller fingerprint forbidden")
 return candidate
