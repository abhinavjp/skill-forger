from .models import SCHEMA_VERSION
def classify_structural_change(anchor_result): return "moved" if anchor_result.get("status")=="moved" else ("ambiguous" if anchor_result.get("status") in ("ambiguous","missing") else "unchanged")
def build_packet(prior_finding,anchor_result,snapshot):
 return {"schema_version":SCHEMA_VERSION,"packet_id":prior_finding["fingerprint"],"prior":prior_finding,"current":{"head_sha":snapshot["head_sha"],"structural_change":classify_structural_change(anchor_result),"anchor":anchor_result,"raw_context":[],"content_hash":""},"relevant_changes":[],"unchanged_evidence":[],"automatic_actions_allowed":anchor_result.get("status") in ("exact","moved")}
