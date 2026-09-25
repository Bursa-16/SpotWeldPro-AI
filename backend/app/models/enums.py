from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    SYSTEM_ADMIN           = "SYSTEM_ADMIN"
    PROCESS_ENGINEER       = "PROCESS_ENGINEER"
    QUALITY_ENGINEER       = "QUALITY_ENGINEER"
    MANUFACTURING_ENGINEER = "MANUFACTURING_ENGINEER"
    MAINTENANCE            = "MAINTENANCE"
    OPERATOR               = "OPERATOR"
    READ_ONLY              = "READ_ONLY"
    CUSTOMER               = "CUSTOMER"

class RiskLevel(StrEnum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"
