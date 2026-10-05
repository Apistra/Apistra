"""Deterministic, fail-closed approval and resource policy evaluation."""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from uuid import UUID, uuid4

from apistra.modules.policies.domain import (
    ApprovalDecision,
    BudgetAction,
    EffectClass,
    LimitBudgetDecision,
    LimitDecision,
    LimitObservation,
    LimitPolicyAuditEvent,
    LimitPolicyStatus,
    LimitPolicyVersion,
    PolicyAuditEvent,
    PolicyDecision,
    PolicyError,
    PolicyErrorCode,
)
from apistra.modules.policies.ports import PolicyClock, PolicyStore

MAXIMUM_ACTION_LENGTH = 128
MAXIMUM_SCOPE_LENGTH = 512
MAXIMUM_POLICY_NAME_LENGTH = 128
MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128
MINIMUM_LIMIT_VALUE = 1
MAXIMUM_LIMIT_VALUE = 9_007_199_254_740_991
MAXIMUM_WARNING_THRESHOLD_PERCENT = 99
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
type PolicyAuditEventList = list[PolicyAuditEvent]
type LimitPolicyVersionList = list[LimitPolicyVersion]
type LimitPolicyAuditEventList = list[LimitPolicyAuditEvent]


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

    def create_limit_policy_version(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        name: str,
        maximum_duration_seconds: int,
        maximum_calls: int,
        maximum_tokens: int,
        maximum_cost_minor_units: int,
        currency: str,
        maximum_concurrency: int,
        rate_limit_requests: int,
        rate_limit_window_seconds: int,
        warning_threshold_percent: int | None,
        idempotency_key: str,
        correlation_id: str,
        *,
        policy_id: UUID | None = None,
        expected_latest_version: int = 0,
    ) -> PolicyResult[LimitPolicyVersion]:
        normalized_name = name.strip()
        normalized_currency = currency.strip().upper()
        values = (
            maximum_duration_seconds,
            maximum_calls,
            maximum_tokens,
            maximum_cost_minor_units,
            maximum_concurrency,
            rate_limit_requests,
            rate_limit_window_seconds,
        )
        validation = self._validate_limit_policy(
            normalized_name,
            normalized_currency,
            values,
            warning_threshold_percent,
            idempotency_key,
        )
        if validation:
            return PolicyResult(error=validation)
        resolved_policy_id = policy_id or uuid4()
        version_number = expected_latest_version + 1
        now = self._clock.now()
        version = LimitPolicyVersion(
            policy_id=resolved_policy_id,
            owner_administrator_id=owner_id,
            project_id=project_id,
            version=version_number,
            status=(
                LimitPolicyStatus.PUBLISHED if version_number == 1 else LimitPolicyStatus.DRAFT
            ),
            name=normalized_name,
            maximum_duration_seconds=maximum_duration_seconds,
            maximum_calls=maximum_calls,
            maximum_tokens=maximum_tokens,
            maximum_cost_minor_units=maximum_cost_minor_units,
            currency=normalized_currency,
            maximum_concurrency=maximum_concurrency,
            rate_limit_requests=rate_limit_requests,
            rate_limit_window_seconds=rate_limit_window_seconds,
            warning_threshold_percent=warning_threshold_percent,
            created_at=now,
            created_by=owner_id,
        )
        event = LimitPolicyAuditEvent(
            id=uuid4(),
            event_type="policy.limit_version_created",
            created_at=now,
            correlation_id=correlation_id,
            actor_id=owner_id,
            actor_username=actor_username,
            project_id=project_id,
            policy_id=resolved_policy_id,
            policy_version=version_number,
            details={"status": version.status, "currency": normalized_currency},
        )
        stored, conflict = self._store.create_limit_policy_version(
            version,
            event,
            idempotency_key,
            self._limit_fingerprint(version),
            expected_latest_version,
        )
        return (
            PolicyResult(value=stored)
            if stored
            else PolicyResult(error=self._limit_store_error(conflict))
        )

    def list_limit_policies(
        self, owner_id: UUID, project_id: UUID
    ) -> PolicyResult[LimitPolicyVersionList]:
        return PolicyResult(value=self._store.list_latest_limit_policies(owner_id, project_id))

    def limit_policy_versions(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID
    ) -> PolicyResult[LimitPolicyVersionList]:
        values = self._store.list_limit_policy_versions(owner_id, project_id, policy_id)
        return PolicyResult(value=values) if values else PolicyResult(error=self._unavailable())

    def exact_limit_policy(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID, version: int
    ) -> PolicyResult[LimitPolicyVersion]:
        value = self._store.get_exact_limit_policy(owner_id, project_id, policy_id, version)
        return PolicyResult(value=value) if value else PolicyResult(error=self._unavailable())

    def exact_limit_policy_available(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID, version: int
    ) -> bool:
        policy = self._store.get_exact_limit_policy(owner_id, project_id, policy_id, version)
        return policy is not None and policy.status is LimitPolicyStatus.PUBLISHED

    def publish_limit_policy_version(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        policy_id: UUID,
        version: int,
        correlation_id: str,
    ) -> PolicyResult[LimitPolicyVersion]:
        event = LimitPolicyAuditEvent(
            id=uuid4(),
            event_type="policy.limit_version_published",
            created_at=self._clock.now(),
            correlation_id=correlation_id,
            actor_id=owner_id,
            actor_username=actor_username,
            project_id=project_id,
            policy_id=policy_id,
            policy_version=version,
            details={"status": LimitPolicyStatus.PUBLISHED},
        )
        published, conflict = self._store.publish_limit_policy_version(
            owner_id, project_id, policy_id, version, event
        )
        return (
            PolicyResult(value=published)
            if published
            else PolicyResult(error=self._limit_store_error(conflict))
        )

    def evaluate_limits(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        policy_id: UUID,
        policy_version: int,
        observation: LimitObservation,
        correlation_id: str,
        protected_effect: Callable[[], None] | None = None,
    ) -> PolicyResult[LimitBudgetDecision]:
        policy = self._store.get_exact_limit_policy(owner_id, project_id, policy_id, policy_version)
        if policy is None:
            return PolicyResult(error=self._unavailable())
        if policy.status is not LimitPolicyStatus.PUBLISHED:
            return PolicyResult(error=self._unavailable())
        validation = self._validate_observation(policy, observation)
        if validation:
            return PolicyResult(error=validation)
        observed = self._observed_values(observation)
        boundaries = self._boundary_values(policy)
        violations = tuple(key for key, value in observed.items() if value > boundaries[key])
        warned = self._warned_limits(policy, observed, boundaries, violations)
        decision, action = self._decision(violations, warned)
        result = LimitBudgetDecision(
            decision=decision,
            action=action,
            project_id=project_id,
            policy_id=policy_id,
            policy_version=policy_version,
            violated_limits=violations,
            warned_limits=warned,
            effect_permitted=decision is not LimitDecision.DENY,
        )
        self._store.record_limit_event(
            LimitPolicyAuditEvent(
                id=uuid4(),
                event_type="policy.limit_evaluated",
                created_at=self._clock.now(),
                correlation_id=correlation_id,
                actor_id=owner_id,
                actor_username=actor_username,
                project_id=project_id,
                policy_id=policy_id,
                policy_version=policy_version,
                details={
                    "boundaries": boundaries,
                    "observed": observed,
                    "currency": policy.currency,
                    "decision": decision,
                    "action": action,
                    "violated_limits": violations,
                    "warned_limits": warned,
                },
            )
        )
        if result.effect_permitted and protected_effect:
            protected_effect()
        return PolicyResult(value=result)

    def limit_audit_events(self, owner_id: UUID) -> PolicyResult[LimitPolicyAuditEventList]:
        return PolicyResult(value=self._store.list_limit_audit_for_owner(owner_id))

    @staticmethod
    def _validate_limit_policy(
        name: str,
        currency: str,
        values: tuple[int, ...],
        warning_threshold_percent: int | None,
        idempotency_key: str,
    ) -> PolicyError | None:
        if not 1 <= len(name) <= MAXIMUM_POLICY_NAME_LENGTH:
            return PolicyService._invalid_error("Policy name must contain 1 to 128 characters.")
        if any(not MINIMUM_LIMIT_VALUE <= value <= MAXIMUM_LIMIT_VALUE for value in values):
            return PolicyService._invalid_error(
                "Every hard limit must be a positive safe JSON integer."
            )
        if not CURRENCY_PATTERN.fullmatch(currency):
            return PolicyService._invalid_error("Currency must be a three-letter uppercase code.")
        if (
            warning_threshold_percent is not None
            and not 1 <= warning_threshold_percent <= MAXIMUM_WARNING_THRESHOLD_PERCENT
        ):
            return PolicyService._invalid_error(
                "Warning threshold must be between 1 and 99 percent."
            )
        if not 1 <= len(idempotency_key) <= MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
            return PolicyService._invalid_error("Idempotency-Key must contain 1 to 128 characters.")
        return None

    @staticmethod
    def _validate_observation(
        policy: LimitPolicyVersion, observation: LimitObservation
    ) -> PolicyError | None:
        values = (
            observation.duration_seconds,
            observation.calls,
            observation.tokens,
            observation.cost_minor_units,
            observation.concurrency,
            observation.requests_in_window,
        )
        if any(not 0 <= value <= MAXIMUM_LIMIT_VALUE for value in values):
            return PolicyService._invalid_error(
                "Observed resource values must be safe JSON integers."
            )
        if observation.rate_window_seconds != policy.rate_limit_window_seconds:
            return PolicyService._invalid_error(
                "Observed rate window must exactly match the policy rate window."
            )
        return None

    @staticmethod
    def _observed_values(observation: LimitObservation) -> dict[str, int]:
        return {
            "maximum_duration": observation.duration_seconds,
            "maximum_calls": observation.calls,
            "maximum_tokens": observation.tokens,
            "maximum_cost": observation.cost_minor_units,
            "maximum_concurrency": observation.concurrency,
            "rate_limit": observation.requests_in_window,
        }

    @staticmethod
    def _boundary_values(policy: LimitPolicyVersion) -> dict[str, int]:
        return {
            "maximum_duration": policy.maximum_duration_seconds,
            "maximum_calls": policy.maximum_calls,
            "maximum_tokens": policy.maximum_tokens,
            "maximum_cost": policy.maximum_cost_minor_units,
            "maximum_concurrency": policy.maximum_concurrency,
            "rate_limit": policy.rate_limit_requests,
        }

    @staticmethod
    def _warned_limits(
        policy: LimitPolicyVersion,
        observed: dict[str, int],
        boundaries: dict[str, int],
        violations: tuple[str, ...],
    ) -> tuple[str, ...]:
        if policy.warning_threshold_percent is None:
            return ()
        return tuple(
            key
            for key, value in observed.items()
            if key not in violations
            and value * 100 >= boundaries[key] * policy.warning_threshold_percent
        )

    @staticmethod
    def _decision(
        violations: tuple[str, ...], warned: tuple[str, ...]
    ) -> tuple[LimitDecision, BudgetAction]:
        if violations:
            return LimitDecision.DENY, BudgetAction.STOP
        if warned:
            return LimitDecision.WARN, BudgetAction.WARN
        return LimitDecision.ALLOW, BudgetAction.ALLOW

    @staticmethod
    def _limit_fingerprint(version: LimitPolicyVersion) -> str:
        payload = {
            key: value
            for key, value in asdict(version).items()
            if key
            not in {
                "policy_id",
                "created_at",
                "created_by",
                "owner_administrator_id",
                "project_id",
            }
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()

    @staticmethod
    def _limit_store_error(conflict: str | None) -> PolicyError:
        if conflict == "version":
            return PolicyError(
                PolicyErrorCode.VERSION_CONFLICT,
                "This draft changed elsewhere. Reload the latest version before saving.",
            )
        if conflict == "idempotency":
            return PolicyError(
                PolicyErrorCode.IDEMPOTENCY_CONFLICT,
                "Idempotency-Key was already used for a different request.",
            )
        if conflict == "unavailable":
            return PolicyService._unavailable()
        return PolicyService._unavailable()

    @staticmethod
    def _unavailable() -> PolicyError:
        return PolicyError(PolicyErrorCode.UNAVAILABLE, "Limit policy version is unavailable.")

    @staticmethod
    def _invalid_error(message: str) -> PolicyError:
        return PolicyError(PolicyErrorCode.INVALID_INPUT, message)

    @staticmethod
    def _invalid(message: str) -> PolicyResult[PolicyDecision]:
        return PolicyResult(error=PolicyError(PolicyErrorCode.INVALID_INPUT, message))
