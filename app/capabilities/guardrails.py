"""
Guardrails capability.

Provides content filtering, PII detection, input/output validation,
and safety checks for agent interactions.
"""
import logging
import re
import hashlib
from typing import Optional, Dict, Any, List, Set, Callable, Awaitable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class GuardrailType(str, Enum):
    """Types of guardrails."""
    INPUT = "input"
    OUTPUT = "output"
    BOTH = "both"


class GuardrailSeverity(str, Enum):
    """Severity levels for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailAction(str, Enum):
    """Actions to take on violations."""
    ALLOW = "allow"          # Allow with warning
    MASK = "mask"            # Mask sensitive content
    BLOCK = "block"          # Block the request
    REPLACE = "replace"      # Replace with safe content


class PIIType(str, Enum):
    """Types of PII to detect."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    NAME = "name"
    ADDRESS = "address"
    CUSTOM = "custom"


class GuardrailViolation(BaseModel):
    """A guardrail violation."""
    id: str = Field(default_factory=lambda: hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:12])
    guardrail_name: str
    guardrail_type: GuardrailType
    severity: GuardrailSeverity
    action_taken: GuardrailAction
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Position in content
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    matched_text: Optional[str] = None


class GuardrailResult(BaseModel):
    """Result of guardrail check."""
    passed: bool = True
    content: str  # Original or modified content
    violations: List[GuardrailViolation] = Field(default_factory=list)
    blocked: bool = False
    modified: bool = False
    
    def add_violation(self, violation: GuardrailViolation):
        self.violations.append(violation)
        if violation.action_taken == GuardrailAction.BLOCK:
            self.passed = False
            self.blocked = True
        elif violation.action_taken in [GuardrailAction.MASK, GuardrailAction.REPLACE]:
            self.modified = True


class GuardrailRule(BaseModel):
    """A guardrail rule definition."""
    name: str
    description: str = ""
    enabled: bool = True
    guardrail_type: GuardrailType = GuardrailType.BOTH
    severity: GuardrailSeverity = GuardrailSeverity.MEDIUM
    action: GuardrailAction = GuardrailAction.BLOCK
    
    # Pattern matching
    patterns: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    # Custom check function name
    custom_check: Optional[str] = None
    
    # Replacement for MASK/REPLACE actions
    replacement: str = "[REDACTED]"


class GuardrailConfig(CapabilityConfig):
    """Guardrails configuration."""
    # PII Detection
    pii_detection_enabled: bool = Field(default=True)
    pii_types: List[PIIType] = Field(
        default_factory=lambda: [PIIType.EMAIL, PIIType.PHONE, PIIType.SSN, PIIType.CREDIT_CARD]
    )
    pii_action: GuardrailAction = Field(default=GuardrailAction.MASK)
    
    # Content filtering
    content_filtering_enabled: bool = Field(default=True)
    blocked_keywords: List[str] = Field(default_factory=list)
    blocked_patterns: List[str] = Field(default_factory=list)
    
    # Toxicity
    toxicity_check_enabled: bool = Field(default=False)
    toxicity_threshold: float = Field(default=0.7)
    
    # Custom rules
    custom_rules: List[GuardrailRule] = Field(default_factory=list)
    
    # Audit
    log_violations: bool = Field(default=True)
    store_violations: bool = Field(default=True)


class GuardrailsManager(Capability):
    """Guardrails capability for content safety."""
    
    name = "guardrails"
    version = "1.0.0"
    description = "Content filtering, PII detection, and safety checks"
    
    # PII Regex patterns
    PII_PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        PIIType.SSN: r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{16}\b',
        PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    def __init__(self, config: Optional[GuardrailConfig] = None):
        super().__init__(config or GuardrailConfig())
        self.config: GuardrailConfig = self.config
        self._violations: List[GuardrailViolation] = []
        self._custom_checks: Dict[str, Callable[[str], Awaitable[List[GuardrailViolation]]]] = {}
    
    async def _do_initialize(self):
        """Initialize guardrails."""
        logger.info(f"Guardrails initialized (PII={self.config.pii_detection_enabled})")
    
    def register_custom_check(
        self, 
        name: str, 
        check_fn: Callable[[str], Awaitable[List[GuardrailViolation]]]
    ):
        """Register a custom check function."""
        self._custom_checks[name] = check_fn
    
    async def check_input(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check input content."""
        return await self._check(content, GuardrailType.INPUT, context)
    
    async def check_output(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check output content."""
        return await self._check(content, GuardrailType.OUTPUT, context)
    
    async def _check(
        self, 
        content: str, 
        check_type: GuardrailType,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Run all guardrail checks."""
        result = GuardrailResult(content=content)
        modified_content = content
        
        # PII Detection
        if self.config.pii_detection_enabled:
            modified_content, pii_violations = await self._check_pii(modified_content)
            for v in pii_violations:
                v.guardrail_type = check_type
                result.add_violation(v)
        
        # Content filtering (blocked keywords)
        if self.config.content_filtering_enabled:
            keyword_violations = await self._check_keywords(modified_content, check_type)
            for v in keyword_violations:
                result.add_violation(v)
                if v.action_taken == GuardrailAction.BLOCK:
                    result.content = modified_content
                    return result
        
        # Pattern matching
        pattern_violations = await self._check_patterns(modified_content, check_type)
        for v in pattern_violations:
            result.add_violation(v)
            if v.action_taken == GuardrailAction.BLOCK:
                result.content = modified_content
                return result
        
        # Custom rules
        for rule in self.config.custom_rules:
            if not rule.enabled:
                continue
            if rule.guardrail_type not in [check_type, GuardrailType.BOTH]:
                continue
            
            rule_violations = await self._check_rule(modified_content, rule)
            for v in rule_violations:
                result.add_violation(v)
                if v.action_taken == GuardrailAction.BLOCK:
                    result.content = modified_content
                    return result
        
        result.content = modified_content
        
        # Store violations
        if self.config.store_violations and result.violations:
            self._violations.extend(result.violations)
        
        return result
    
    async def _check_pii(self, content: str) -> tuple:
        """Check for PII and optionally mask it."""
        violations = []
        modified = content
        
        for pii_type in self.config.pii_types:
            pattern = self.PII_PATTERNS.get(pii_type)
            if not pattern:
                continue
            
            for match in re.finditer(pattern, modified, re.IGNORECASE):
                violation = GuardrailViolation(
                    guardrail_name=f"pii_{pii_type.value}",
                    guardrail_type=GuardrailType.BOTH,
                    severity=GuardrailSeverity.HIGH,
                    action_taken=self.config.pii_action,
                    message=f"Detected {pii_type.value}",
                    start_pos=match.start(),
                    end_pos=match.end(),
                    matched_text=match.group() if self.config.pii_action != GuardrailAction.BLOCK else "[hidden]",
                    details={"pii_type": pii_type.value}
                )
                violations.append(violation)
                
                if self.config.pii_action == GuardrailAction.MASK:
                    replacement = f"[{pii_type.value.upper()}_REDACTED]"
                    modified = modified[:match.start()] + replacement + modified[match.end():]
        
        return modified, violations
    
    async def _check_keywords(self, content: str, check_type: GuardrailType) -> List[GuardrailViolation]:
        """Check for blocked keywords."""
        violations = []
        content_lower = content.lower()
        
        for keyword in self.config.blocked_keywords:
            if keyword.lower() in content_lower:
                violations.append(GuardrailViolation(
                    guardrail_name="blocked_keyword",
                    guardrail_type=check_type,
                    severity=GuardrailSeverity.HIGH,
                    action_taken=GuardrailAction.BLOCK,
                    message=f"Blocked keyword detected",
                    details={"keyword": keyword}
                ))
        
        return violations
    
    async def _check_patterns(self, content: str, check_type: GuardrailType) -> List[GuardrailViolation]:
        """Check against blocked patterns."""
        violations = []
        
        for pattern in self.config.blocked_patterns:
            try:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(GuardrailViolation(
                        guardrail_name="blocked_pattern",
                        guardrail_type=check_type,
                        severity=GuardrailSeverity.HIGH,
                        action_taken=GuardrailAction.BLOCK,
                        message="Blocked pattern detected",
                        details={"pattern": pattern}
                    ))
            except re.error as e:
                logger.warning(f"Invalid pattern {pattern}: {e}")
        
        return violations
    
    async def _check_rule(self, content: str, rule: GuardrailRule) -> List[GuardrailViolation]:
        """Check content against a custom rule."""
        violations = []
        
        # Check patterns
        for pattern in rule.patterns:
            try:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    violations.append(GuardrailViolation(
                        guardrail_name=rule.name,
                        guardrail_type=rule.guardrail_type,
                        severity=rule.severity,
                        action_taken=rule.action,
                        message=rule.description or f"Rule '{rule.name}' violated",
                        start_pos=match.start(),
                        end_pos=match.end(),
                        matched_text=match.group()
                    ))
            except re.error:
                pass
        
        # Check keywords
        content_lower = content.lower()
        for keyword in rule.keywords:
            if keyword.lower() in content_lower:
                violations.append(GuardrailViolation(
                    guardrail_name=rule.name,
                    guardrail_type=rule.guardrail_type,
                    severity=rule.severity,
                    action_taken=rule.action,
                    message=rule.description or f"Rule '{rule.name}' violated",
                    details={"keyword": keyword}
                ))
        
        # Custom check
        if rule.custom_check and rule.custom_check in self._custom_checks:
            custom_violations = await self._custom_checks[rule.custom_check](content)
            violations.extend(custom_violations)
        
        return violations
    
    async def get_violations(
        self,
        limit: int = 100,
        severity: Optional[GuardrailSeverity] = None
    ) -> List[GuardrailViolation]:
        """Get stored violations."""
        violations = self._violations
        if severity:
            violations = [v for v in violations if v.severity == severity]
        return violations[-limit:]
    
    async def clear_violations(self):
        """Clear stored violations."""
        self._violations.clear()
    
    async def add_rule(self, rule: GuardrailRule):
        """Add a custom rule."""
        self.config.custom_rules.append(rule)
    
    async def remove_rule(self, rule_name: str) -> bool:
        """Remove a custom rule."""
        for i, rule in enumerate(self.config.custom_rules):
            if rule.name == rule_name:
                del self.config.custom_rules[i]
                return True
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get guardrail statistics."""
        by_severity = {}
        by_type = {}
        
        for v in self._violations:
            by_severity[v.severity.value] = by_severity.get(v.severity.value, 0) + 1
            by_type[v.guardrail_name] = by_type.get(v.guardrail_name, 0) + 1
        
        return {
            "total_violations": len(self._violations),
            "by_severity": by_severity,
            "by_type": by_type,
            "pii_detection_enabled": self.config.pii_detection_enabled,
            "custom_rules_count": len(self.config.custom_rules)
        }
