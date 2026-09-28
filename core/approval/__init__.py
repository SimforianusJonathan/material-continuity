"""Deterministic approval policy and validation boundary."""

from .engine import ALLOWED_ACTIONS_BY_ROLE, validate_approval
from .models import (
    ApprovalBlockReason,
    ApprovalGateDecision,
    ApprovalGateInputError,
    ApprovalGateStatus,
    ApprovalValidationRequest,
    ApproverRole,
    AuthenticatedPrincipal,
    ControlledAction,
)

__all__ = [
    "ALLOWED_ACTIONS_BY_ROLE",
    "ApprovalBlockReason",
    "ApprovalGateDecision",
    "ApprovalGateInputError",
    "ApprovalGateStatus",
    "ApprovalValidationRequest",
    "ApproverRole",
    "AuthenticatedPrincipal",
    "ControlledAction",
    "validate_approval",
]
