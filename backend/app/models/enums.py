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


class OrgRole(StrEnum):
    ORG_ADMIN = "ORG_ADMIN"
    APPROVER  = "APPROVER"
    ENGINEER  = "ENGINEER"
    VIEWER    = "VIEWER"


class ProfileStatus(StrEnum):
    DRAFT           = "DRAFT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    VALIDATED       = "VALIDATED"
    APPROVED        = "APPROVED"
    ACTIVE          = "ACTIVE"
    SUPERSEDED      = "SUPERSEDED"
    REVOKED         = "REVOKED"


class ProfileApprovalEventType(StrEnum):
    CREATED              = "CREATED"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    REVIEWED             = "REVIEWED"
    VALIDATED            = "VALIDATED"
    APPROVED             = "APPROVED"
    ACTIVATED            = "ACTIVATED"
    SUPERSEDED           = "SUPERSEDED"
    REVOKED              = "REVOKED"
