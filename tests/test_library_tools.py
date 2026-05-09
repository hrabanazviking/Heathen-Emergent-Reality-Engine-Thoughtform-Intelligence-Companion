"""
Tests for Library sense tool definitions — LIBRARY_TOOL_DEFINITIONS.

These tests verify the structural contract of the locked tool schemas.
No Forge implementation is required — these verify the scaffold.

Covers:
    - LIBRARY_TOOL_DEFINITIONS is a list with exactly 3 entries
    - Each entry has the required OpenAI tool schema structure
    - Tool names are exactly the 3 locked names
    - Required parameter lists are correct
    - No tool has additionalProperties set to True
    - library.search has 'query' as required, 'max_results' as optional
    - library.get_text has 'source_id' as required, others optional
    - library.list_sources has no required parameters

Ref: src/heretic/skilningr/senses/library/tools.py
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
"""

from __future__ import annotations

import pytest

from heretic.skilningr.senses.library.tools import LIBRARY_TOOL_DEFINITIONS

LOCKED_TOOL_NAMES = {
    "library.search",
    "library.get_text",
    "library.list_sources",
}


class TestLibraryToolDefinitionsStructure:
    """Verify the OpenAI tool schema structure of LIBRARY_TOOL_DEFINITIONS."""

    def test_is_list(self) -> None:
        assert isinstance(LIBRARY_TOOL_DEFINITIONS, list)

    def test_exactly_three_tools(self) -> None:
        assert len(LIBRARY_TOOL_DEFINITIONS) == 3

    def test_all_have_type_function(self) -> None:
        for defn in LIBRARY_TOOL_DEFINITIONS:
            assert defn.get("type") == "function"

    def test_all_have_function_block(self) -> None:
        for defn in LIBRARY_TOOL_DEFINITIONS:
            assert "function" in defn
            fn = defn["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn

    def test_tool_names_match_locked_set(self) -> None:
        names = {d["function"]["name"] for d in LIBRARY_TOOL_DEFINITIONS}
        assert names == LOCKED_TOOL_NAMES

    def test_no_additional_properties(self) -> None:
        """Each tool's parameter schema must have additionalProperties: False."""
        for defn in LIBRARY_TOOL_DEFINITIONS:
            params = defn["function"]["parameters"]
            assert params.get("additionalProperties") is False, (
                f"Tool {defn['function']['name']!r} allows additionalProperties."
            )

    def test_all_descriptions_non_empty(self) -> None:
        for defn in LIBRARY_TOOL_DEFINITIONS:
            fn = defn["function"]
            assert len(fn["description"]) > 0


class TestLibrarySearchSchema:
    """Verify library.search parameter schema."""

    def _get_tool(self) -> dict:
        for d in LIBRARY_TOOL_DEFINITIONS:
            if d["function"]["name"] == "library.search":
                return d
        raise AssertionError("library.search not found")

    def test_query_is_required(self) -> None:
        tool = self._get_tool()
        required = tool["function"]["parameters"].get("required", [])
        assert "query" in required

    def test_max_results_is_optional(self) -> None:
        tool = self._get_tool()
        required = tool["function"]["parameters"].get("required", [])
        assert "max_results" not in required

    def test_query_type_is_string(self) -> None:
        tool = self._get_tool()
        props = tool["function"]["parameters"]["properties"]
        assert props["query"]["type"] == "string"

    def test_max_results_type_is_integer(self) -> None:
        tool = self._get_tool()
        props = tool["function"]["parameters"]["properties"]
        assert props["max_results"]["type"] == "integer"


class TestLibraryGetTextSchema:
    """Verify library.get_text parameter schema."""

    def _get_tool(self) -> dict:
        for d in LIBRARY_TOOL_DEFINITIONS:
            if d["function"]["name"] == "library.get_text":
                return d
        raise AssertionError("library.get_text not found")

    def test_source_id_is_required(self) -> None:
        tool = self._get_tool()
        required = tool["function"]["parameters"].get("required", [])
        assert "source_id" in required

    def test_start_line_is_optional(self) -> None:
        tool = self._get_tool()
        required = tool["function"]["parameters"].get("required", [])
        assert "start_line" not in required

    def test_num_lines_is_optional(self) -> None:
        tool = self._get_tool()
        required = tool["function"]["parameters"].get("required", [])
        assert "num_lines" not in required


class TestLibraryListSourcesSchema:
    """Verify library.list_sources parameter schema."""

    def _get_tool(self) -> dict:
        for d in LIBRARY_TOOL_DEFINITIONS:
            if d["function"]["name"] == "library.list_sources":
                return d
        raise AssertionError("library.list_sources not found")

    def test_no_required_parameters(self) -> None:
        tool = self._get_tool()
        required = tool["function"]["parameters"].get("required", [])
        assert required == []

    def test_no_properties(self) -> None:
        tool = self._get_tool()
        props = tool["function"]["parameters"].get("properties", {})
        assert props == {}
