"""
Tests A-M for IP-CLEANUP-02B2-R4.
Run against PATCHED module files in scratchpad.
"""
import sys
import os
import dataclasses
import importlib
import importlib.util
import types

SP = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Minimal stub modules so patched domain files can be imported without the
# full app stack.
# ---------------------------------------------------------------------------

def _stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


from enum import StrEnum

class EvidenceClass(StrEnum):
    UNRESOLVED = "UNRESOLVED"
    SOURCE_BACKED = "SOURCE_BACKED"
    ADVISORY = "ADVISORY"

class RuleLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"

_stub("app")
_stub("app.domain")
_stub("app.domain.governance_types",
      EvidenceClass=EvidenceClass,
      RuleLifecycleStatus=RuleLifecycleStatus,
      RegistryAuthorityError=Exception,
      ContentVersionMetadata=None)
_stub("app.domain.models",
      minitab_doe_predict=lambda d: types.SimpleNamespace(model_name="doe", prediction_mm=4.5, confidence="low", status="ok"),
      oem_table_prediction=lambda a,b: types.SimpleNamespace(model_name="oem", prediction_mm=5.0, confidence="high", status="ok"),
      literature_4sqrt_t=lambda t: types.SimpleNamespace(model_name="lit", prediction_mm=3.5, confidence="medium", status="ok"))

# ---------------------------------------------------------------------------
# Load patched modules from scratchpad by renaming file imports
# ---------------------------------------------------------------------------

def _load_patched(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

rrt = _load_patched("app.domain.rule_registry_types",
                    f"{SP}/rule_registry_types_patched.py")
re_mod = _load_patched("app.domain.rules_engine",
                       f"{SP}/rules_engine_patched.py")
mr_mod = _load_patched("app.domain.model_registry",
                       f"{SP}/model_registry_patched.py")

# Also load ORM module stub for test H/I/J
_stub("app.db")
_stub("app.db.session", Base=object)
_stub("sqlalchemy")
_stub("sqlalchemy.orm")
_stub("app.models")
_stub("app.models.entities", utc_now=None)
_stub("app.models.governance",
      ImmutableJSON=None,
      freeze_json_attribute=lambda x: None,
      portable_enum=lambda e, n: None,
      protect_immutable_model=lambda x: None)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

PASS = []
FAIL = []

def check(label, condition, detail=""):
    if condition:
        PASS.append(label)
        print(f"  PASS  {label}")
    else:
        FAIL.append(label)
        print(f"  FAIL  {label}" + (f": {detail}" if detail else ""))


# ===========================================================================
# A. active Rule has authority_level, not source_type
# ===========================================================================
rule_fields = {f.name for f in dataclasses.fields(re_mod.Rule)}
check("A: Rule has authority_level field", "authority_level" in rule_fields)
check("A: Rule has no source_type field", "source_type" not in rule_fields)

# ===========================================================================
# B. active Rule has reference_profile_id, not source_name
# ===========================================================================
check("B: Rule has reference_profile_id field", "reference_profile_id" in rule_fields)
check("B: Rule has no source_name field", "source_name" not in rule_fields)

# ===========================================================================
# C. EvidenceReferenceDraft has no provenance identity fields
# ===========================================================================
draft_fields = {f.name for f in dataclasses.fields(rrt.EvidenceReferenceDraft)}
prohibited_draft = {"source_type", "source_name", "source_document", "edition",
                    "section_reference", "page_reference", "table_reference", "reference_uri"}
for pf in prohibited_draft:
    check(f"C: EvidenceReferenceDraft has no {pf}", pf not in draft_fields)

# ===========================================================================
# D. public analysis output contains no prohibited source_* fields
# ===========================================================================
result = re_mod.evaluate_compliance(
    material_family="Tümü",
    stack_count="Tümü",
    t_min=1.0,
    values={
        "cooling_flow_lpm": 8.0,
        "cooling_temp_c": 20.0,
        "dc_current": True,
        "nugget_min_mm": 5.0,
    }
)
prohibited_output = {"source_type", "source_name", "source_document", "source_url"}
output_keys = set()
for r in result.get("results", []):
    output_keys.update(r.keys())
for pk in prohibited_output:
    check(f"D: evaluate_compliance output has no {pk}", pk not in output_keys)

# ===========================================================================
# E. rule priority ordering: REFERENCE_LEVEL_01 < REFERENCE_LEVEL_02 etc.
# ===========================================================================
prio = re_mod.AUTHORITY_PRIORITY
check("E: priority order L01 < L02", prio.get("REFERENCE_LEVEL_01", 99) < prio.get("REFERENCE_LEVEL_02", 99))
check("E: priority order L02 < L03", prio.get("REFERENCE_LEVEL_02", 99) < prio.get("REFERENCE_LEVEL_03", 99))
check("E: priority order L04 < L05", prio.get("REFERENCE_LEVEL_04", 99) < prio.get("REFERENCE_LEVEL_05", 99))
check("E: priority order L05 < L06", prio.get("REFERENCE_LEVEL_05", 99) < prio.get("REFERENCE_LEVEL_06", 99))

# ===========================================================================
# F. compliance outcomes unchanged (pass/fail for known inputs)
# ===========================================================================
r2 = re_mod.evaluate_compliance(
    material_family="Tümü",
    stack_count="Tümü",
    t_min=1.0,
    values={
        "cooling_flow_lpm": 3.0,   # fails min 6.0
        "cooling_temp_c": 30.0,    # fails max 25.0
        "dc_current": True,
        "nugget_min_mm": 5.0,      # passes derived_min 4*sqrt(1)=4.0
    }
)
statuses = {r["rule_id"]: r["status"] for r in r2["results"]}
check("F: COOL_FLOW_MIN_01 fails for 3.0 L/dk", statuses.get("COOL_FLOW_MIN_01") == "Uygun Değil")
check("F: COOL_TEMP_MAX_01 fails for 30C", statuses.get("COOL_TEMP_MAX_01") == "Uygun Değil")
check("F: NUGGET_MIN_DERIVED_01 passes for 5.0 >= 4.0", statuses.get("NUGGET_MIN_DERIVED_01") == "Uygun")

# ===========================================================================
# G. numeric engineering outputs unchanged
# ===========================================================================
import math
r3 = re_mod.evaluate_compliance(
    material_family="Tümü",
    stack_count="Tümü",
    t_min=0.8,
    values={"cooling_flow_lpm": 7.0, "cooling_temp_c": 22.0, "dc_current": True, "nugget_min_mm": 4.5}
)
nugget_result = next((r for r in r3["results"] if r["rule_id"] == "NUGGET_MIN_DERIVED_01"), None)
expected_min = 4.0 * math.sqrt(0.8)
# expected field looks like ">= 3.58 mm" — extract the numeric part
def _parse_threshold(s):
    parts = s.split()
    for p in parts:
        try:
            return float(p)
        except ValueError:
            pass
    return None
check("G: nugget_min_mm derived threshold = 4*sqrt(0.8)",
      nugget_result is not None and abs((_parse_threshold(nugget_result["expected"]) or 0) - expected_min) < 0.01)

# ===========================================================================
# H. repository writes NULL to legacy provenance columns (ORM construction)
# ===========================================================================
# We test the patched repository file's text directly since ORM imports are heavy
with open(f"{SP}/rule_registry_repository_patched.py", "r", encoding="utf-8") as f:
    repo_src = f.read()
check("H: repo sets source_type=None LEGACY", "source_type=None,  # LEGACY_PERSISTENCE_ONLY" in repo_src)
check("H: repo sets source_name=None LEGACY", "source_name=None,  # LEGACY_PERSISTENCE_ONLY" in repo_src)
check("H: repo sets source_document=None LEGACY", "source_document=None,  # LEGACY_PERSISTENCE_ONLY" in repo_src)
check("H: repo sets source_url=None LEGACY", "source_url=None,  # LEGACY_PERSISTENCE_ONLY" in repo_src)

# ===========================================================================
# I. LegacyRuleSourceType has correct historical values
# ===========================================================================
with open(f"{SP}/rule_registry_patched.py", "r", encoding="utf-8") as f:
    orm_src = f.read()

required_vals = ["OEM", "ISO", "AWS", "SEP", "COMPANY_STANDARD", "FIELD_MODEL", "LITERATURE", "DERIVED"]
for v in required_vals:
    check(f"I: LegacyRuleSourceType has {v}", f'    {v} = "{v}"' in orm_src)
check("I: LegacyRuleSourceType marked LEGACY_PERSISTENCE_ONLY", "class LegacyRuleSourceType(StrEnum):  # LEGACY_PERSISTENCE_ONLY" in orm_src)

# ===========================================================================
# J. no active domain module imports LegacyRuleSourceType
# ===========================================================================
with open(f"{SP}/rule_registry_types_patched.py", "r", encoding="utf-8") as f:
    rrt_src = f.read()
with open(f"{SP}/rules_engine_patched.py", "r", encoding="utf-8") as f:
    re_src = f.read()
with open(f"{SP}/model_registry_patched.py", "r", encoding="utf-8") as f:
    mr_src = f.read()

check("J: rule_registry_types does not import LegacyRuleSourceType", "LegacyRuleSourceType" not in rrt_src)
check("J: rules_engine does not import LegacyRuleSourceType", "LegacyRuleSourceType" not in re_src)
check("J: model_registry does not import LegacyRuleSourceType", "LegacyRuleSourceType" not in mr_src)

# ===========================================================================
# K. migration 0003 SHA256 unchanged
# ===========================================================================
import hashlib
migration_path = "/root/.claude/uploads/69ba75da-08ae-55ed-9b62-eacc7ae5b7a9/e1ee8b19-1790853850900_0003_registry_foundation.py"
with open(migration_path, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest().upper()
expected_sha = "047ED28F83F15FB5DFB39FE443951C8292CB738148B46669AE5515147D773603"
check("K: migration 0003 SHA256 matches", sha == expected_sha, f"got {sha}")

# ===========================================================================
# L. model registry emits model_basis not source_type
# ===========================================================================
mr_fields = {f.name for f in dataclasses.fields(mr_mod.RegisteredModel)}
check("L: RegisteredModel has model_basis", "model_basis" in mr_fields)
check("L: RegisteredModel has no source_type", "source_type" not in mr_fields)
rows = mr_mod.registry_dataframe_rows()
check("L: registry rows use model_basis key", all("model_basis" in r for r in rows))
check("L: registry rows have no source_type key", all("source_type" not in r for r in rows))
check("L: REFERENCE_TABLE value present", any(r["model_basis"] == "REFERENCE_TABLE" for r in rows))
check("L: EXPERIMENTAL_MODEL value present", any(r["model_basis"] == "EXPERIMENTAL_MODEL" for r in rows))
check("L: DERIVED_CRITERION value present", any(r["model_basis"] == "DERIVED_CRITERION" for r in rows))

# ===========================================================================
# M. no TypeError or import error when importing patched domain modules
# ===========================================================================
try:
    rule = re_mod.Rule(
        rule_id="TEST", name="Test", authority_level="REFERENCE_LEVEL_01",
        reference_profile_id="REF_PROFILE_01", parameter="cooling_flow_lpm",
        operator="min", min_value=5.0, max_value=None, unit="L/dk",
        material_family="Tümü", stack_count="Tümü", note="test"
    )
    check("M: Rule instantiation no TypeError", True)
    check("M: Rule priority works", rule.priority == 1)
except Exception as e:
    check("M: Rule instantiation no TypeError", False, str(e))

try:
    draft = rrt.EvidenceReferenceDraft(
        evidence_id="E1", evidence_revision="1",
        evidence_class=EvidenceClass.UNRESOLVED,
        lifecycle_status=RuleLifecycleStatus.DRAFT,
        created_by_actor_id="test@test.com"
    )
    check("M: EvidenceReferenceDraft instantiation no TypeError", True)
except Exception as e:
    check("M: EvidenceReferenceDraft instantiation no TypeError", False, str(e))

# ===========================================================================
# Summary
# ===========================================================================
total = len(PASS) + len(FAIL)
print(f"\n{'='*60}")
print(f"RESULTS: {len(PASS)}/{total} passed")
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print(f"  - {f}")
else:
    print("ALL TESTS PASSED")
print("="*60)
sys.exit(0 if not FAIL else 1)
