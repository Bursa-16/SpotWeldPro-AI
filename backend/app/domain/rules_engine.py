
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import math


AUTHORITY_PRIORITY = {
    "REFERENCE_LEVEL_01": 1,
    "REFERENCE_LEVEL_02": 2,
    "REFERENCE_LEVEL_03": 3,
    "REFERENCE_LEVEL_04": 4,
    "REFERENCE_LEVEL_05": 5,
    "REFERENCE_LEVEL_06": 6,
}


@dataclass
class Rule:
    rule_id: str
    name: str
    authority_level: str
    reference_profile_id: str
    parameter: str
    operator: str
    min_value: Optional[float]
    max_value: Optional[float]
    unit: str
    material_family: str
    stack_count: str
    note: str
    enabled: bool = True

    @property
    def priority(self) -> int:
        return AUTHORITY_PRIORITY.get(self.authority_level, 99)


DEFAULT_RULES: List[Rule] = [
    Rule(
        rule_id="COOL_FLOW_MIN_01",
        name="Minimum soğutma debisi",
        authority_level="REFERENCE_LEVEL_02",
        reference_profile_id="REF_PROFILE_01",
        parameter="cooling_flow_lpm",
        operator="min",
        min_value=6.0,
        max_value=None,
        unit="L/dk",
        material_family="Tümü",
        stack_count="Tümü",
        note="Minimum soğutma debisi gereksinimi."
    ),
    Rule(
        rule_id="COOL_TEMP_MAX_01",
        name="Maksimum soğutma suyu sıcaklığı",
        authority_level="REFERENCE_LEVEL_02",
        reference_profile_id="REF_PROFILE_01",
        parameter="cooling_temp_c",
        operator="max",
        min_value=None,
        max_value=25.0,
        unit="°C",
        material_family="Tümü",
        stack_count="Tümü",
        note="Maksimum soğutma suyu sıcaklığı gereksinimi."
    ),
    Rule(
        rule_id="DC_CURRENT_REQUIRED_01",
        name="DC akım zorunluluğu",
        authority_level="REFERENCE_LEVEL_02",
        reference_profile_id="REF_PROFILE_01",
        parameter="dc_current",
        operator="equals",
        min_value=1.0,
        max_value=1.0,
        unit="bool",
        material_family="Tümü",
        stack_count="Tümü",
        note="DC akım gereksinimi."
    ),
    Rule(
        rule_id="TIP_DIAMETER_07_09_01",
        name="0,7–0,9 mm için elektrot uç çapı",
        authority_level="REFERENCE_LEVEL_01",
        reference_profile_id="REF_PROFILE_02",
        parameter="tip_diameter_mm",
        operator="range",
        min_value=5.0,
        max_value=5.0,
        unit="mm",
        material_family="Düşük / Orta Karbonlu Çelik",
        stack_count="Tümü",
        note="En ince sac 0,7–0,9 mm olduğunda."
    ),
    Rule(
        rule_id="NUGGET_MIN_DERIVED_01",
        name="Minimum çekirdek çapı 4√t",
        authority_level="REFERENCE_LEVEL_05",
        reference_profile_id="REF_PROFILE_03",
        parameter="nugget_min_mm",
        operator="derived_min",
        min_value=None,
        max_value=None,
        unit="mm",
        material_family="Tümü",
        stack_count="Tümü",
        note="En ince sac kalınlığına göre hesaplanır."
    ),
]


def rules_to_rows(rules: Optional[List[Rule]] = None) -> List[Dict[str, Any]]:
    return [asdict(r) | {"priority": r.priority} for r in (rules or DEFAULT_RULES)]


def _matches(rule: Rule, material_family: str, stack_count: str) -> bool:
    material_ok = rule.material_family in ("Tümü", material_family)
    stack_ok = rule.stack_count in ("Tümü", stack_count)
    return rule.enabled and material_ok and stack_ok


def _evaluate_rule(rule: Rule, values: Dict[str, Any], t_min: float) -> Dict[str, Any]:
    value = values.get(rule.parameter)
    expected = ""
    status = "İnceleme Gerekli"
    passed = None

    if rule.operator == "derived_min":
        expected_value = 4.0 * math.sqrt(t_min)
        actual = float(values.get("nugget_min_mm", 0.0))
        passed = actual >= expected_value
        expected = f">= {expected_value:.2f} {rule.unit}"
        value = actual
    elif rule.operator == "min":
        passed = float(value) >= float(rule.min_value)
        expected = f">= {rule.min_value} {rule.unit}"
    elif rule.operator == "max":
        passed = float(value) <= float(rule.max_value)
        expected = f"<= {rule.max_value} {rule.unit}"
    elif rule.operator == "range":
        passed = float(rule.min_value) <= float(value) <= float(rule.max_value)
        expected = f"{rule.min_value}–{rule.max_value} {rule.unit}"
    elif rule.operator == "equals":
        passed = float(bool(value)) == float(rule.min_value)
        expected = "Evet" if rule.min_value == 1.0 else str(rule.min_value)
    else:
        expected = "Tanımsız operatör"

    if passed is True:
        status = "Uygun"
    elif passed is False:
        status = "Uygun Değil"

    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.name,
        "priority": rule.priority,
        "parameter": rule.parameter,
        "actual_value": value,
        "expected": expected,
        "status": status,
        "note": rule.note,
    }


def detect_conflicts(rules: List[Rule]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    grouped: Dict[Tuple[str, str, str], List[Rule]] = {}

    for rule in rules:
        if not rule.enabled:
            continue
        key = (rule.parameter, rule.material_family, rule.stack_count)
        grouped.setdefault(key, []).append(rule)

    for key, items in grouped.items():
        if len(items) < 2:
            continue

        ordered = sorted(items, key=lambda r: r.priority)
        winner = ordered[0]

        for challenger in ordered[1:]:
            conflict = False
            if winner.operator == challenger.operator == "range":
                wmin, wmax = winner.min_value, winner.max_value
                cmin, cmax = challenger.min_value, challenger.max_value
                conflict = max(wmin, cmin) > min(wmax, cmax)
            elif winner.operator == challenger.operator == "min":
                conflict = winner.min_value != challenger.min_value
            elif winner.operator == challenger.operator == "max":
                conflict = winner.max_value != challenger.max_value
            elif winner.operator == challenger.operator == "equals":
                conflict = winner.min_value != challenger.min_value

            if conflict:
                conflicts.append({
                    "parameter": key[0],
                    "material_family": key[1],
                    "stack_count": key[2],
                    "winner_rule_id": winner.rule_id,
                    "challenger_rule_id": challenger.rule_id,
                    "decision": "Öncelikli mühendislik kuralı uygulandı.",
                })

    return conflicts


def evaluate_compliance(
    *,
    material_family: str,
    stack_count: str,
    t_min: float,
    values: Dict[str, Any],
    custom_rules: Optional[List[Rule]] = None,
) -> Dict[str, Any]:
    all_rules = list(DEFAULT_RULES)
    if custom_rules:
        all_rules.extend(custom_rules)

    applicable = [r for r in all_rules if _matches(r, material_family, stack_count)]
    results = [_evaluate_rule(r, values, t_min) for r in applicable]

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "Uygun")
    failed = sum(1 for r in results if r["status"] == "Uygun Değil")
    review = total - passed - failed
    score = (passed / total * 100.0) if total else 0.0

    return {
        "results": results,
        "conflicts": detect_conflicts(applicable),
        "summary": {
            "total_rules": total,
            "passed": passed,
            "failed": failed,
            "review": review,
            "score": score,
        },
    }


def build_custom_rule(data: Dict[str, Any]) -> Rule:
    return Rule(
        rule_id=str(data["rule_id"]).strip(),
        name=str(data["name"]).strip(),
        authority_level=str(data["authority_level"]).strip(),
        reference_profile_id=str(data["reference_profile_id"]).strip(),
        parameter=str(data["parameter"]).strip(),
        operator=str(data["operator"]).strip(),
        min_value=data.get("min_value"),
        max_value=data.get("max_value"),
        unit=str(data.get("unit", "")).strip(),
        material_family=str(data.get("material_family", "Tümü")).strip(),
        stack_count=str(data.get("stack_count", "Tümü")).strip(),
        note=str(data.get("note", "")).strip(),
        enabled=bool(data.get("enabled", True)),
    )
