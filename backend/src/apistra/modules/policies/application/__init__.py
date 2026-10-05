"""Deterministic, fail-closed approval policy evaluation."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from apistra.modules.policies.domain import (
    ApprovalDecision,
    EffectClass,
    PolicyAuditEvent,
    PolicyDecision,
    PolicyError,
    PolicyErrorCode,
)
from apistra.modules.policies.ports import PolicyClock, PolicyStore

MAXIMUM_ACTION_LENGTH = 128
MAXIMUM_SCOPE_LENGTH = 512
type PolicyAuditEventList = list[PolicyAuditEvent]


@dataclass(frozen=True, slots=True)
class PolicyResult[T]:
    value: T | None = None
    error: PolicyError | None = None


class PolicyService:
    def __init__(self, store: PolicyStore, clock: PolicyClock) -> None:
        self._store = store
        self._clock = clock

    @staticmethod
    def classify(value: str) -> PolicyResult[EffectClass]:
        try:
            return PolicyResult(value=EffectClass(value))
        except ValueError:
            return PolicyResult(
                error=PolicyError(
                    PolicyErrorCode.INVALID_INPUT,
                    "Effect class must be READ, WRITE, or ADMINISTRATIVE.",
                )
            )

    def evaluate(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        tool_id: UUID,
        tool_version: int,
        effect_class: EffectClass,
        action: str,
        scope: str,
        correlation_id: str,
        *,
        timed_out: bool = False,
    ) -> PolicyResult[PolicyDecision]:
        normalized_action = action.strip()
        normalized_scope = scope.strip()
        if not 1 <= len(normalized_action) <= MAXIMUM_ACTION_LENGTH:
            return self._invalid("Action must contain 1 to 128 characters.")
        if not 1 <= len(normalized_scope) <= MAXIMUM_SCOPE_LENGTH:
            return self._invalid("Scope must contain 1 to 512 characters.")
        evaluated_at = self._clock.now()
        exception = None
        if timed_out:
            decision = ApprovalDecision.DENY
        elif effect_class is EffectClass.READ:
            decision = ApprovalDecision.ALLOW
        else:
            exception = self._store.find_exact_exception(
                owner_id,
                project_id,
                tool_id,
                tool_version,
                normalized_action,
                normalized_scope,
                evaluated_at,
            )
            decision = (
                ApprovalDecision.ALLOW
                if exception is not None
                else ApprovalDecision.REQUIRE_APPROVAL
            )
        result = PolicyDecision(
            decision=decision,
            project_id=project_id,
            tool_id=tool_id,
            tool_version=tool_version,
            action=normalized_action,
            scope=normalized_scope,
            exception_id=exception.id if exception else None,
        )
        self._store.record_event(
            PolicyAuditEvent(
                id=uuid4(),
                event_type="policy.tool_effect_evaluated",
                created_at=evaluated_at,
                correlation_id=correlation_id,
                actor_id=owner_id,
                actor_username=actor_username,
                project_id=project_id,
                tool_id=tool_id,
                tool_version=tool_version,
                details={
                    "action": normalized_action,
                    "scope": normalized_scope,
                    "effect_class": effect_class,
                    "decision": decision,
                    "exception_id": str(exception.id) if exception else None,
                    "timed_out": timed_out,
                },
            )
        )
        return PolicyResult(value=result)

    def audit_events(self, owner_id: UUID) -> PolicyResult[PolicyAuditEventList]:
        return PolicyResult(value=self._store.list_audit_for_owner(owner_id))

    @staticmethod
    def _invalid(message: str) -> PolicyResult[PolicyDecision]:
        return PolicyResult(error=PolicyError(PolicyErrorCode.INVALID_INPUT, message))
