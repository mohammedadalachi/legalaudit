# forward-chaining rule evaluator
# checks each rule from knowledge_base.py against the contract text
# and logs why a rule fired (the "explanation facility")

import re
import logging
import traceback

log = logging.getLogger("legalaudit.inference")

try:
    from knowledge_base import get_rules_for_doc_type
except ImportError as exc:
    log.critical("Cannot import knowledge_base: %s", exc)
    raise

RISK_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# rule IDs that are mutually exclusive - empty for now
EXPLICIT_CONFLICT_PAIRS: set = set()

_REQUIRED_RULE_KEYS = ("id", "name", "statute", "description",
                        "keywords", "check_type", "risk", "priority",
                        "recommendation")


# main entry point
def analyse(text: str, doc_type: str) -> dict:
    """
    Main entry point.
    Input:  text (str), doc_type ("employment" | "tenancy")
    Output: structured report dict with findings + reasoning traces.
    Never raises , always returns a dict, with "error" key set on failure.
    """
    try:
        # Input type validation
        if not isinstance(text, str):
            return _error_response(
                doc_type,
                f"Expected text to be a string, got {type(text).__name__}."
            )
        if not isinstance(doc_type, str):
            doc_type = "employment"

        if doc_type not in ("employment", "tenancy"):
            return _error_response(
                doc_type,
                f"Unknown document type '{doc_type}'. "
                "Please select 'Employment Contract' or 'Residential Tenancy Agreement'."
            )

        if not text or len(text.strip()) < 50:
            return _error_response(
                doc_type,
                "Document text is too short or empty. Please upload a valid contract."
            )

        normalised = _normalise(text)

        # Relevance check
        relevance_error = _check_document_relevance(normalised, doc_type)
        if relevance_error:
            return _error_response(doc_type, relevance_error)

        # Load rules
        try:
            rules = get_rules_for_doc_type(doc_type)
        except Exception as e:
            log.error("Failed to load rules for doc_type='%s': %s", doc_type, e)
            return _error_response(
                doc_type,
                "Could not load the rule database. Please contact support."
            )

        if not rules:
            log.warning("No rules found for doc_type='%s'", doc_type)
            return _error_response(
                doc_type,
                f"No rules are defined for document type '{doc_type}'."
            )

        # Evaluate rules
        raw_findings = []
        for rule in rules:
            try:
                _validate_rule_schema(rule)
                result = _evaluate_rule(rule, normalised)
                if result is not None:
                    raw_findings.append(result)
            except _RuleSchemaError as e:
                log.error("Skipping malformed rule %s: %s",
                          rule.get("id", "?"), e)
                # Skip this rule, continue auditing
            except Exception as e:
                log.error("Unexpected error evaluating rule %s: %s\n%s",
                          rule.get("id", "?"), e, traceback.format_exc())
                # Soft-fail: skip this rule rather than crashing the whole audit

        findings = _resolve_conflicts(raw_findings)
        findings.sort(key=lambda f: RISK_ORDER.get(f.get("risk", "LOW"), 0), reverse=True)

        # Collect passed rules
        flagged_ids = {f["rule_id"] for f in findings}
        passed_rules = [
            {
                "rule_id":    r["id"],
                "name":       r["name"],
                "statute":    r["statute"],
                "check_type": r["check_type"]
            }
            for r in rules if r["id"] not in flagged_ids
        ]

        summary = {
            "doc_type":           doc_type,
            "total_rules_checked": len(rules),
            "issues_found":       len(findings),
            "compliant":          len(rules) - len(findings),
            "high_risk":          sum(1 for f in findings if f.get("risk") == "HIGH"),
            "medium_risk":        sum(1 for f in findings if f.get("risk") == "MEDIUM"),
            "low_risk":           sum(1 for f in findings if f.get("risk") == "LOW"),
            "overall_status":     _overall_status(findings),
            "overall_code":       _overall_code(findings)
        }

        return {
            "error":        None,
            "findings":     findings,
            "passed_rules": passed_rules,
            "summary":      summary,
            "doc_type":     doc_type
        }

    except Exception as e:
        log.error("Unhandled crash in analyse(): %s\n%s", e, traceback.format_exc())
        return _error_response(
            doc_type if isinstance(doc_type, str) else "unknown",
            f"The analysis engine crashed unexpectedly: {e}"
        )


# helpers
def _error_response(doc_type: str, message: str) -> dict:
    """Consistent error return for analyse()."""
    return {
        "error":    message,
        "findings": [],
        "summary":  {},
        "doc_type": doc_type
    }


class _RuleSchemaError(Exception):
    """Raised when a rule dict is missing required keys."""


def _validate_rule_schema(rule: dict):
    """Raise _RuleSchemaError if the rule is structurally invalid."""
    if not isinstance(rule, dict):
        raise _RuleSchemaError(f"Rule is not a dict: {type(rule).__name__}")
    missing = [k for k in _REQUIRED_RULE_KEYS if k not in rule]
    if missing:
        raise _RuleSchemaError(
            f"Rule {rule.get('id', '?')} is missing keys: {missing}"
        )
    if not isinstance(rule["keywords"], list) or not rule["keywords"]:
        raise _RuleSchemaError(
            f"Rule {rule['id']} has empty or invalid 'keywords' list."
        )
    if rule["check_type"] not in ("presence", "risk_keyword"):
        raise _RuleSchemaError(
            f"Rule {rule['id']} has unknown check_type: '{rule['check_type']}'."
        )
    if rule["risk"] not in ("HIGH", "MEDIUM", "LOW"):
        raise _RuleSchemaError(
            f"Rule {rule['id']} has invalid risk level: '{rule['risk']}'."
        )


# rule evaluation
def _evaluate_rule(rule: dict, normalised_text: str) -> dict | None:
    """
    Evaluate a single rule and build a full reasoning trace.
    Returns a finding dict (with reasoning_chain) or None if rule passes.
    """
    keywords      = rule["keywords"]
    found_keyword = _find_matching_keyword(keywords, normalised_text)
    keyword_found = found_keyword is not None

    # Build reasoning chain
    reasoning = []
    reasoning.append(
        f"Activated rule {rule['id']}: \"{rule['name']}\" [{rule['statute']}]"
    )
    reasoning.append(
        "Check type: "
        + ("PRESENCE , clause must exist in document"
           if rule["check_type"] == "presence"
           else "RISK KEYWORD , clause exists but requires scrutiny")
    )
    preview_keywords = keywords[:4]
    suffix = " ..." if len(keywords) > 4 else ""
    reasoning.append(
        f"Searched for {len(keywords)} keyword(s): "
        f"{', '.join(repr(k) for k in preview_keywords)}{suffix}"
    )

    if keyword_found:
        reasoning.append(f"Result: Keyword '{found_keyword}' was found in the document")
    else:
        reasoning.append("Result: None of the required keywords were found in the document")

    # Special case: E018 Minimum Wage , check actual salary value
    if rule["id"] == "E018":
        salary = _extract_monthly_salary(normalised_text)
        if salary is not None:
            if salary >= 1700:
                reasoning.append(
                    f"Salary detected: RM {salary:,} , meets the RM 1,700 "
                    "minimum wage requirement. Rule passes."
                )
                return None
            else:
                # Below minimum , flag regardless of whether keyword present
                reasoning.append(
                    f"Salary detected: RM {salary:,} , BELOW the RM 1,700 "
                    "national minimum wage (Minimum Wages Order 2022)."
                )
                risk     = rule['risk']
                priority = rule['priority']
                reasoning.append(f"Risk assigned: {risk} (priority {priority}/10)")
                reasoning.append("Finding status: FLAGGED , ILLEGAL CLAUSE VALUE")
                return _make_finding(rule, "ILLEGAL CLAUSE VALUE", found_keyword, reasoning)

    # Special case: E001 Notice Period , validate duration is legal
    if rule["id"] == "E001" and keyword_found:
        if not _validate_notice_period(normalised_text):
            risk     = rule['risk']
            priority = rule['priority']
            reasoning.append(
                "Validation failed: Notice period found but duration is below "
                "the 4-week legal minimum under Section 12, or a "
                "'without notice' termination clause was detected."
            )
            reasoning.append(f"Risk assigned: {risk} (priority {priority}/10)")
            reasoning.append("Finding status: FLAGGED , ILLEGAL CLAUSE VALUE")
            return _make_finding(rule, "ILLEGAL CLAUSE VALUE", None, reasoning)
        else:
            # Notice period exists and is legally sufficient , pass
            reasoning.append(
                "Validation passed: Notice period found and meets the 4-week minimum. "
                "Rule passes."
            )
            return None

    # Standard presence check
    if rule["check_type"] == "presence" and not keyword_found:
        reasoning.append(
            f"Condition triggered: Required clause is ABSENT → violates {rule['statute']}"
        )
        risk     = rule['risk']
        priority = rule['priority']
        reasoning.append(f"Risk assigned: {risk} (priority {priority}/10)")
        reasoning.append("Finding status: FLAGGED , MISSING CLAUSE")
        return _make_finding(rule, "MISSING CLAUSE", None, reasoning)

    # Risk keyword check
    elif rule["check_type"] == "risk_keyword" and keyword_found:
        reasoning.append(
            f"Condition triggered: Risky clause DETECTED via keyword "
            f"'{found_keyword}' → requires legal scrutiny under {rule['statute']}"
        )
        risk     = rule['risk']
        priority = rule['priority']
        reasoning.append(f"Risk assigned: {risk} (priority {priority}/10)")
        reasoning.append("Finding status: FLAGGED , REQUIRES REVIEW")
        return _make_finding(rule, "REQUIRES REVIEW", found_keyword, reasoning)

    # Rule passed
    else:
        if rule["check_type"] == "presence":
            reasoning.append(
                "Condition: Clause is PRESENT , rule passes. No finding raised."
            )
        else:
            reasoning.append(
                "Condition: No risky keyword detected , rule passes. No finding raised."
            )
        return None


def _make_finding(rule: dict, issue_type: str,
                  matched_keyword, reasoning: list) -> dict:
    return {
        "rule_id":         rule["id"],
        "name":            rule["name"],
        "statute":         rule["statute"],
        "description":     rule["description"],
        "risk":            rule["risk"],
        "priority":        rule["priority"],
        "issue_type":      issue_type,
        "recommendation":  rule["recommendation"],
        "matched_keyword": matched_keyword,
        "reasoning_chain": reasoning
    }


# conflict resolution
def _resolve_conflicts(findings: list) -> list:
    """
    Only suppress findings that belong to an explicitly declared conflict pair.
    All other findings are reported independently.
    """
    if not EXPLICIT_CONFLICT_PAIRS or len(findings) <= 1:
        return findings

    suppressed_ids = set()
    for pair in EXPLICIT_CONFLICT_PAIRS:
        matched = [f for f in findings if f.get("rule_id") in pair]
        if len(matched) < 2:
            continue
        winner = max(matched, key=lambda f: (
            f.get("priority", 0), RISK_ORDER.get(f.get("risk", "LOW"), 0)
        ))
        for f in matched:
            if f.get("rule_id") != winner.get("rule_id"):
                suppressed_ids.add(f.get("rule_id"))

    return [f for f in findings if f.get("rule_id") not in suppressed_ids]


# text matching
def _find_matching_keyword(keywords: list, text: str) -> str | None:
    """Return the first matched keyword string, or None if none found."""
    for kw in keywords:
        try:
            kw_clean    = _normalise(kw)
            kw_flexible = kw_clean.replace("-", "[- ]?")
            if re.search(r"\b" + kw_flexible + r"\b", text):
                return kw
        except re.error as e:
            log.warning("Regex error for keyword '%s': %s , skipping", kw, e)
    return None


def _check_document_relevance(text: str, doc_type: str) -> str | None:
    """
    Checks whether the uploaded document is plausibly the right type.
    Returns an error string if the document seems wrong, None if it looks fine.
    Prevents false findings on invoices, letters, random PDFs etc.
    """
    employment_signals = [
        "employee", "employer", "employment", "salary", "wages",
        "position", "job", "work", "probation", "termination",
        "contract of service", "appointment", "commission"
    ]
    tenancy_signals = [
        "tenant", "landlord", "tenancy", "rental", "rent", "property",
        "premises", "lease", "deposit", "monthly rental", "letting"
    ]

    try:
        if doc_type == "employment":
            hits = sum(1 for w in employment_signals if w in text)
            if hits < 2:
                return (
                    "This document does not appear to be an employment contract. "
                    "Please upload a valid employment contract and select the correct document type."
                )
        elif doc_type == "tenancy":
            hits = sum(1 for w in tenancy_signals if w in text)
            if hits < 2:
                return (
                    "This document does not appear to be a tenancy agreement. "
                    "Please upload a valid tenancy agreement and select the correct document type."
                )
    except Exception as e:
        log.warning("Relevance check failed: %s , skipping check", e)
        # If the relevance check itself crashes, let the audit proceed
    return None


def _validate_notice_period(text: str) -> bool:
    """
    Returns True only if the document contains a legally sufficient notice
    period (>= 4 weeks / 28 days / 1 month).
    Returns False if:
      - Any hours-based notice is found (e.g. "24 hours notice")
      - Any days-based notice under 28 days is found
      - "without prior notice" or "without notice" appears anywhere
    """
    try:
        # "without notice" is only a violation when it sits in a termination
        # sentence , not in unrelated phrases like "paid without notice of delay".
        termination_ctx = re.compile(
            r"terminat|dismiss|discharg|fired|summary\s+dismissal|end\s+of\s+employ",
            re.IGNORECASE
        )
        without_notice_pat = re.compile(
            r"without\s+(prior\s+)?notice", re.IGNORECASE
        )
        for sentence in re.split(r"[.;]\s*", text):
            if without_notice_pat.search(sentence) and termination_ctx.search(sentence):
                return False
        insufficient = re.findall(
            r"(\d+)\s*(hour|day)s?\s*(?:written\s*)?notice",
            text, re.IGNORECASE
        )
        for value_str, unit in insufficient:
            try:
                value = int(value_str)
            except ValueError:
                continue
            if unit.lower() == "hour":
                return False
            if unit.lower() == "day" and value < 28:
                return False
            if unit.lower() == "day" and value >= 28:
                return True   # 28 days == 4 weeks == legal minimum
        # Pattern A: "4 weeks notice" / "4 weeks written notice"
        valid_a = re.findall(
            r"(\d+)\s*(week|month)s?\s*(?:written\s*)?notice",
            text, re.IGNORECASE
        )
        for value_str, unit in valid_a:
            try:
                value = int(value_str)
            except ValueError:
                continue
            if unit.lower() == "week" and value >= 4:
                return True
            if unit.lower() == "month" and value >= 1:
                return True
        # Pattern B: "written notice of 4 weeks" / "notice of 1 month"
        valid_b = re.findall(
            r"(?:written\s+)?notice\s+of\s+(\d+)\s*(week|month)s?",
            text, re.IGNORECASE
        )
        for value_str, unit in valid_b:
            try:
                value = int(value_str)
            except ValueError:
                continue
            if unit.lower() == "week" and value >= 4:
                return True
            if unit.lower() == "month" and value >= 1:
                return True
    except Exception as e:
        log.warning("Error in _validate_notice_period: %s , defaulting to False", e)
    return False


def _extract_monthly_salary(text: str) -> int | None:
    """
    Extracts the first plausible monthly salary figure (RM 500–RM 50,000).
    Returns None if no figure is found.
    """
    try:
        matches = re.findall(r"rm\s*(\d[\d,]*)", text, re.IGNORECASE)
        for m in matches:
            try:
                value = int(m.replace(",", ""))
                if 500 <= value <= 50000:
                    return value
            except ValueError:
                continue
    except Exception as e:
        log.warning("Error in _extract_monthly_salary: %s", e)
    return None


def _normalise(text: str) -> str:
    """Lowercase, replace OCR noise characters, collapse whitespace."""
    try:
        text = text.lower()
        text = re.sub(r"[|\\]", "l", text)
        # Normalise OCR-introduced hyphens (e.g. "over-time" → "over time").
        # Must run BEFORE whitespace collapse so consecutive spaces are merged.
        text = text.replace("-", " ")
        text = re.sub(r"\s+", " ", text)
        return text
    except Exception as e:
        log.warning("Error normalising text: %s", e)
        return text.lower() if isinstance(text, str) else ""


# overall status
def _overall_status(findings: list) -> str:
    high   = sum(1 for f in findings if f.get("risk") == "HIGH")
    medium = sum(1 for f in findings if f.get("risk") == "MEDIUM")
    if high >= 3:
        return "CRITICAL , Multiple high-risk issues detected. Legal review strongly recommended before signing."
    elif high >= 1:
        return "AT RISK , High-risk issue(s) detected. Recommend legal review before signing."
    elif medium >= 2:
        return "REVIEW NEEDED , Medium-risk issues detected. Consider professional review."
    elif findings:
        return "MINOR ISSUES , Low-risk observations only. Review recommended."
    else:
        return "PASS , No major issues detected. Basic compliance checks passed."


def _overall_code(findings: list) -> str:
    high   = sum(1 for f in findings if f.get("risk") == "HIGH")
    medium = sum(1 for f in findings if f.get("risk") == "MEDIUM")
    if high >= 3:   return "CRITICAL"
    if high >= 1:   return "RISK"
    if medium >= 2: return "REVIEW"
    if findings:    return "MINOR"
    return "PASS"
