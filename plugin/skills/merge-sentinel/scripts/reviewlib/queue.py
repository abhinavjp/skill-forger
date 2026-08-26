import hashlib
from .models import MAX_EXPANSION_LEASES
class QueueError(ValueError): pass
def new_queue(snapshot_id): return {"schema_version":1,"snapshot_id":snapshot_id,"revision":0,"entries":{},"leases":{},"evidence_cache":{}}
def request_lease(state,invariant_id,evidence_key):
 key=hashlib.sha256((invariant_id+"\0"+evidence_key).encode()).hexdigest(); entry=state["entries"].setdefault(key,{"entry_key":key,"invariant_id":invariant_id,"evidence_key":evidence_key,"state":"pending","lease_count":0,"active_lease_id":None,"evidence_hash":None})
 if entry["state"] not in ("pending","unresolved") or entry["lease_count"]>=MAX_EXPANSION_LEASES: raise QueueError("lease unavailable")
 n=entry["lease_count"]+1; lid=hashlib.sha256((state["snapshot_id"]+"\0"+key+"\0"+str(n)).encode()).hexdigest()[:24]; entry.update(state="leased",lease_count=n,active_lease_id=lid); state["leases"][lid]={"lease_id":lid,"entry_key":key,"snapshot_id":state["snapshot_id"],"number":n,"completed":False,"outcome":None}; state["revision"]+=1; return state
def complete_lease(state,lease_id,outcome,evidence_hash):
 lease=state["leases"].get(lease_id)
 if not lease or lease["completed"]: raise QueueError("invalid lease")
 entry=state["entries"][lease["entry_key"]]; lease.update(completed=True,outcome=outcome); entry.update(state=outcome,active_lease_id=None,evidence_hash=evidence_hash); state["revision"]+=1; return state
