from __future__ import annotations
import hashlib
from enum import Enum
from .models import ValidationError, require_schema, normalize_repo_path
class AnchorStatus(str,Enum): EXACT="exact"; MOVED="moved"; AMBIGUOUS="ambiguous"; MISSING="missing"
def normalize_context(lines):
 if not isinstance(lines,list): raise ValidationError("context lines required")
 rows=[]
 for line in lines:
  if not isinstance(line,str): raise ValidationError("context line must be string")
  text=line.replace("\r\n","\n").replace("\r","\n").strip()
  if text: rows.append(text)
 if not 3<=len(rows)<=12: raise ValidationError("context requires 3-12 nonblank lines")
 return "\n".join(rows)
def context_hash(lines): return hashlib.sha256(normalize_context(lines).encode("utf-8")).hexdigest()
def _result(status,method="none",confidence="unresolved",selected=None,candidates=None):
 return {"schema_version":1,"status":status,"method":method,"confidence":confidence,"anchor_identity":("context:"+context_hash(selected["context_lines"]) if selected else "missing:"),"selected":selected if status in ("exact","moved") else None,"candidates":candidates or [],"evidence":[],"reasons":[]}
def resolve_anchor(request):
 require_schema(request); prior=request["prior"]; provider=request["provider"]; candidates=request.get("target_candidates",[])
 path=normalize_repo_path(prior["path"]); wanted=context_hash(prior["context_lines"])
 for candidate in candidates: candidate["path"]=normalize_repo_path(candidate["path"])
 exact=[x for x in candidates if x["path"]==provider.get("new_path") and x.get("blob_sha")==provider.get("new_blob_sha") and x.get("line")==provider.get("new_line")]
 if len(exact)==1:return _result("exact","provider-position","deterministic",exact[0])
 if len(exact)>1:return _result("ambiguous",candidates=exact)
 context=[x for x in candidates if not x.get("binary") and not x.get("generated") and context_hash(x["context_lines"])==wanted]
 renamed=[x for x in context if x["path"]==provider.get("new_path")]
 if provider.get("renamed") and len(renamed)==1:return _result("moved","provider-rename","deterministic",renamed[0])
 if len(context)==1:return _result("exact" if context[0]["path"]==path else "moved","context-hash","corroborated",context[0])
 return _result("ambiguous",candidates=context) if context else _result("missing")
