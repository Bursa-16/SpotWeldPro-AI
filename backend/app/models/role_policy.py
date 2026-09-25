from __future__ import annotations

from app.models.enums import UserRole

LEGACY_ROLE_TO_CANONICAL: dict[str, UserRole] = {
    "System Admin":           UserRole.SYSTEM_ADMIN,
    "Process Engineer":       UserRole.PROCESS_ENGINEER,
    "Quality Engineer":       UserRole.QUALITY_ENGINEER,
    "Manufacturing Engineer": UserRole.MANUFACTURING_ENGINEER,
    "Maintenance":            UserRole.MAINTENANCE,
    "Operator":               UserRole.OPERATOR,
    "Read Only":              UserRole.READ_ONLY,
    "Customer":               UserRole.CUSTOMER,
}


def normalize_user_role(role: str) -> str:
    """READ-PATH normalizer (dual-read shim). Unknown values pass through."""
    return LEGACY_ROLE_TO_CANONICAL.get(role, role)


def canonicalize_role(role: str) -> UserRole:
    """WRITE-PATH validator/canonicalizer. Raises ValueError for unknown values."""
    if role in LEGACY_ROLE_TO_CANONICAL:
        return LEGACY_ROLE_TO_CANONICAL[role]
    try:
        return UserRole(role)
    except ValueError:
        valid = sorted(r.value for r in UserRole)
        raise ValueError(
            f"Unknown role {role!r}. "
            f"Accepted canonical codes: {valid}. "
            f"Legacy display labels are also accepted during the migration window."
        )
