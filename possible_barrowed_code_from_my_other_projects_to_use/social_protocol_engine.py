"""Social protocol guidance and cultural compliance for Norse Saga turns."""

from __future__ import annotations

import json
import csv
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class SocialProtocolEngine:
    """Loads chart-backed social norms and enforces culture-safe turn outputs."""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._protocol_sources: Dict[str, Any] = {}
        self._load_protocol_sources()

    def _load_protocol_sources(self) -> None:
        """Muninn gathers social wisdom from chart scrolls."""
        charts_dir = self.data_path / "charts"
        source_patterns = [
            "*social*.json",
            "*social*.yaml",
            "*social*.jsonl",
            "*social*.csv",
            "*social*.cvs",
            "*social*.txt",
            "*social*.html",
            "*social*.htm",
            "*social*.xml",
            "*social*.pdf",
            "*social*.md",
            "*protocol*.json",
            "*protocol*.yaml",
            "*protocol*.jsonl",
            "*protocol*.csv",
            "*protocol*.cvs",
            "*protocol*.txt",
            "*protocol*.html",
            "*protocol*.htm",
            "*protocol*.xml",
            "*protocol*.pdf",
            "*protocol*.md",
            "*honor*.json",
            "*honor*.yaml",
            "*honor*.jsonl",
            "*honor*.csv",
            "*honor*.cvs",
            "*honor*.txt",
            "*honor*.html",
            "*honor*.htm",
            "*honor*.xml",
            "*honor*.pdf",
            "*rules*.md",
            "*rules*.txt",
            "*rules*.html",
            "*rules*.xml",
            "*rules*.pdf",
            "viking_values.yaml",
            "viking_cultural_practices.yaml",
        ]
        seen: set[str] = set()
        for pattern in source_patterns:
            for chart_path in charts_dir.glob(pattern):
                if chart_path.name in seen:
                    continue
                seen.add(chart_path.name)
                try:
                    suffix = chart_path.suffix.lower()
                    if suffix in {".yaml", ".yml"}:
                        with chart_path.open("r", encoding="utf-8") as handle:
                            self._protocol_sources[chart_path.name] = yaml.safe_load(handle) or {}
                    elif suffix == ".json":
                        with chart_path.open("r", encoding="utf-8") as handle:
                            self._protocol_sources[chart_path.name] = json.load(handle)
                    elif suffix == ".jsonl":
                        with chart_path.open("r", encoding="utf-8") as handle:
                            entries = []
                            for line in handle:
                                line = line.strip()
                                if not line or line.startswith("#"):
                                    continue
                                entries.append(json.loads(line))
                            self._protocol_sources[chart_path.name] = entries
                    elif suffix in {".csv", ".cvs"}:
                        with chart_path.open("r", encoding="utf-8") as handle:
                            self._protocol_sources[chart_path.name] = [row for row in csv.DictReader(handle)]
                    elif suffix == ".pdf":
                        self._protocol_sources[chart_path.name] = self._extract_pdf_text(chart_path)
                    elif suffix in {".md", ".txt", ".html", ".htm", ".xml"}:
                        self._protocol_sources[chart_path.name] = chart_path.read_text(encoding="utf-8")
                except Exception as exc:
                    logger.warning("Could not load social protocol chart %s: %s", chart_path.name, exc)

    def _extract_pdf_text(self, chart_path: Path) -> str:
        module_name = "pypdf" if importlib.util.find_spec("pypdf") else "PyPDF2"
        if not importlib.util.find_spec(module_name):
            logger.warning("No PDF reader installed; skipping PDF protocol source: %s", chart_path)
            return ""
        pdf_module = importlib.import_module(module_name)
        reader = pdf_module.PdfReader(str(chart_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    def get_turn_guidance(
        self,
        action: str,
        state: Dict[str, Any],
        npcs_present: List[Dict[str, Any]],
        ai_complete: Optional[Any] = None,
    ) -> str:
        """Create a compact social protocol block for this turn."""
        roles = self._extract_present_roles(npcs_present)
        chart_directives = self._collect_chart_directives(action=action, roles=roles)
        guidance_lines: List[str] = [
            "Apply only chart-grounded 9th-century Norse social protocol for this scene.",
            "Keep language and behavior culturally grounded to the current setting and caste structure.",
        ]
        if roles:
            guidance_lines.append(f"Active social roles in scene: {', '.join(roles)}.")
        if chart_directives:
            guidance_lines.append("Chart directives:\n- " + "\n- ".join(chart_directives[:8]))

        ai_guidance = self._derive_ai_protocol_guidance(
            action=action,
            state=state,
            chart_directives=chart_directives,
            ai_complete=ai_complete,
        )
        if ai_guidance:
            guidance_lines.append(f"Situation protocol focus: {ai_guidance}")
        return "\n".join(guidance_lines)

    def validate_response(
        self,
        action: str,
        response: str,
        turn_guidance: str,
        ai_complete: Optional[Any] = None,
    ) -> Tuple[bool, str]:
        """Gate output against social protocol; return reroll guidance if needed."""
        if not response.strip():
            return False, "Response was empty; regenerate with stronger cultural grounding."

        local_violations = self._heuristic_violations(response)
        if local_violations:
            return False, "; ".join(local_violations)
        if not ai_complete:
            return True, ""

        judge_prompt = (
            "Judge whether this narration follows the social protocol directives. "
            "Return strict JSON with keys: compliant (bool), reason (string), correction (string).\n\n"
            f"Player action: {action}\n"
            f"Social protocol directives:\n{turn_guidance}\n\n"
            f"Narration to validate:\n{response}"
        )
        try:
            verdict = ai_complete(
                prompt=judge_prompt,
                system_prompt="You are a strict 9th-century Norse cultural validator.",
            )
            parsed = self._safe_json_parse(verdict)
            if parsed and not parsed.get("compliant", True):
                correction = str(parsed.get("correction") or parsed.get("reason") or "Cultural mismatch.")
                return False, correction
        except Exception as exc:
            logger.warning("Social protocol AI validator failed: %s", exc)
        return True, ""

    def _derive_ai_protocol_guidance(
        self,
        action: str,
        state: Dict[str, Any],
        chart_directives: List[str],
        ai_complete: Optional[Any],
    ) -> str:
        """Huginn scouts turn-specific protocol emphasis."""
        if not ai_complete:
            return ""
        compact_state = {
            "location": state.get("current_sub_location_id") or state.get("current_location_id"),
            "time_of_day": state.get("time_of_day"),
            "season": state.get("season"),
            "chaos_factor": state.get("chaos_factor"),
        }
        directives_block = "\n".join(f"- {directive}" for directive in chart_directives[:10])
        prompt = (
            "Using only the listed chart directives, produce one short line for the top social protocol "
            "to prioritize this turn.\n"
            f"Action: {action}\n"
            f"State: {json.dumps(compact_state, ensure_ascii=False)}\n"
            f"Available chart directives:\n{directives_block}"
        )
        try:
            guidance = ai_complete(
                prompt=prompt,
                system_prompt="You summarize social protocol grounded in Viking chart directives only.",
            )
            return str(guidance).strip()
        except Exception as exc:
            logger.warning("Could not derive AI social guidance: %s", exc)
            return ""

    def _collect_chart_directives(self, action: str, roles: List[str]) -> List[str]:
        """Find protocol excerpts relevant to this turn from loaded chart sources."""
        directives: List[str] = []
        tokens = [token for token in action.lower().split() if len(token) > 2]
        role_tokens = [role.lower() for role in roles]

        for _, payload in self._protocol_sources.items():
            flattened = self._flatten_text(payload)
            for snippet in flattened:
                snippet_lower = snippet.lower()
                token_match = any(token in snippet_lower for token in tokens[:10])
                role_match = any(role in snippet_lower for role in role_tokens)
                if token_match or role_match:
                    directives.append(snippet.strip())
                if len(directives) >= 20:
                    return directives
        return directives

    def _flatten_text(self, payload: Any) -> List[str]:
        """Flatten structured chart content into compact snippets."""
        snippets: List[str] = []
        if isinstance(payload, str):
            for raw_line in payload.splitlines():
                line = raw_line.strip(" -#\t")
                if len(line) > 25:
                    snippets.append(line)
            return snippets

        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, (str, int, float)):
                    text = f"{key}: {value}".strip()
                    if len(text) > 25:
                        snippets.append(text)
                else:
                    snippets.extend(self._flatten_text(value))
            return snippets

        if isinstance(payload, list):
            for item in payload:
                snippets.extend(self._flatten_text(item))
            return snippets

        return snippets

    def _extract_present_roles(self, npcs_present: List[Dict[str, Any]]) -> List[str]:
        roles: List[str] = []
        for npc in npcs_present:
            identity = npc.get("identity", {}) if isinstance(npc, dict) else {}
            candidate_role = identity.get("social_class") or npc.get("social_class")
            if candidate_role and candidate_role not in roles:
                roles.append(str(candidate_role))
        return roles

    def _heuristic_violations(self, response: str) -> List[str]:
        """Catch obvious cultural mismatches before LLM judge."""
        response_lower = response.lower()
        violations: List[str] = []
        banned_anachronisms = [
            "smartphone",
            "internet",
            "electricity",
            "social media",
            "gunpowder",
            "democracy",
        ]
        for term in banned_anachronisms:
            if term in response_lower:
                violations.append(f"Anachronistic element detected: {term}")
        return violations

    def _safe_json_parse(self, payload: Any) -> Optional[Dict[str, Any]]:
        if payload is None:
            return None
        text = str(payload).strip()
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except Exception:
                    return None
        return None
