"""
Tests — SMIDJA_TOOL_DEFINITIONS schema correctness.

These tests run immediately (no NotImplementedError in tools.py). They lock the
tool schema contract so that any accidental rename or schema drift is caught.

v0.6.0: 6 tools (Brúarhönd half)
v0.6.1: +3 tools (Forge half) = 9 total

Ref: src/heretic/skilningr/senses/smidja/tools.py
     docs/architecture/SENSE_CONTRACTS.md §2 (tool naming)
"""

import pytest

from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS


def test_tool_definitions_count():
    """Exactly 9 tool definitions must be present in v0.6.1 (6 Brúarhönd + 3 Forge)."""
    assert len(SMIDJA_TOOL_DEFINITIONS) == 9


def test_all_tools_are_function_type():
    """Every tool definition must have type='function'."""
    for tool in SMIDJA_TOOL_DEFINITIONS:
        assert tool["type"] == "function", f"Bad type on tool: {tool}"


def test_tool_names_are_two_part_smidja_prefix():
    """Every tool name must start with 'smidja.' (two-part format per SENSE_CONTRACTS §2)."""
    for tool in SMIDJA_TOOL_DEFINITIONS:
        name = tool["function"]["name"]
        assert name.startswith("smidja."), f"Tool name does not start with smidja.: {name!r}"
        parts = name.split(".")
        assert len(parts) == 2, f"Tool name must be exactly two parts: {name!r}"


def test_tool_names_exact_set():
    """The 9 tool names must match the locked v0.6.1 names exactly."""
    expected_names = {
        # Brúarhönd half (v0.6.0)
        "smidja.screenshot",
        "smidja.click",
        "smidja.type_text",
        "smidja.hotkey",
        "smidja.vroid_open",
        "smidja.vroid_export",
        # Forge half (v0.6.1)
        "smidja.forge_build_avatar",
        "smidja.forge_get_avatar",
        "smidja.forge_inspect_avatar",
    }
    actual_names = {tool["function"]["name"] for tool in SMIDJA_TOOL_DEFINITIONS}
    assert actual_names == expected_names


def test_all_tools_have_description():
    """Every tool must have a non-empty description string."""
    for tool in SMIDJA_TOOL_DEFINITIONS:
        desc = tool["function"].get("description", "")
        assert isinstance(desc, str) and len(desc) > 0, (
            f"Missing description on tool: {tool['function']['name']}"
        )


def test_all_tools_have_parameters_object():
    """Every tool must have a parameters dict with type='object'."""
    for tool in SMIDJA_TOOL_DEFINITIONS:
        params = tool["function"].get("parameters", {})
        assert params.get("type") == "object", (
            f"parameters.type must be 'object' on: {tool['function']['name']}"
        )


def test_click_requires_x_and_y():
    """smidja.click must declare x and y as required parameters."""
    click = next(t for t in SMIDJA_TOOL_DEFINITIONS if t["function"]["name"] == "smidja.click")
    required = click["function"]["parameters"].get("required", [])
    assert "x" in required
    assert "y" in required


def test_type_text_requires_text():
    """smidja.type_text must declare text as a required parameter."""
    tt = next(t for t in SMIDJA_TOOL_DEFINITIONS if t["function"]["name"] == "smidja.type_text")
    required = tt["function"]["parameters"].get("required", [])
    assert "text" in required


def test_hotkey_requires_keys():
    """smidja.hotkey must declare keys as a required parameter."""
    hk = next(t for t in SMIDJA_TOOL_DEFINITIONS if t["function"]["name"] == "smidja.hotkey")
    required = hk["function"]["parameters"].get("required", [])
    assert "keys" in required


def test_vroid_open_requires_project_path():
    """smidja.vroid_open must declare project_path as required."""
    vo = next(t for t in SMIDJA_TOOL_DEFINITIONS if t["function"]["name"] == "smidja.vroid_open")
    required = vo["function"]["parameters"].get("required", [])
    assert "project_path" in required


def test_vroid_export_requires_output_path():
    """smidja.vroid_export must declare output_path as required."""
    ve = next(t for t in SMIDJA_TOOL_DEFINITIONS if t["function"]["name"] == "smidja.vroid_export")
    required = ve["function"]["parameters"].get("required", [])
    assert "output_path" in required


def test_screenshot_has_no_required_parameters():
    """smidja.screenshot has no required parameters (region is optional)."""
    ss = next(t for t in SMIDJA_TOOL_DEFINITIONS if t["function"]["name"] == "smidja.screenshot")
    required = ss["function"]["parameters"].get("required", [])
    assert required == []


def test_no_duplicate_tool_names():
    """Tool names must be unique across the definitions list."""
    names = [t["function"]["name"] for t in SMIDJA_TOOL_DEFINITIONS]
    assert len(names) == len(set(names)), f"Duplicate tool names found: {names}"


# ---------------------------------------------------------------------------
# Forge tool schema tests (v0.6.1)
# ---------------------------------------------------------------------------

def test_forge_tools_have_forge_prefix():
    """All Forge tools must have action names starting with 'forge_'."""
    forge_tools = [
        t for t in SMIDJA_TOOL_DEFINITIONS
        if t["function"]["name"].split(".", 1)[1].startswith("forge_")
    ]
    assert len(forge_tools) == 3
    forge_names = {t["function"]["name"] for t in forge_tools}
    assert forge_names == {
        "smidja.forge_build_avatar",
        "smidja.forge_get_avatar",
        "smidja.forge_inspect_avatar",
    }


def test_forge_build_avatar_requires_loom_spec():
    """smidja.forge_build_avatar must declare loom_spec as required."""
    ba = next(
        t for t in SMIDJA_TOOL_DEFINITIONS
        if t["function"]["name"] == "smidja.forge_build_avatar"
    )
    required = ba["function"]["parameters"].get("required", [])
    assert "loom_spec" in required
    props = ba["function"]["parameters"].get("properties", {})
    assert "loom_spec" in props
    assert props["loom_spec"]["type"] == "object"


def test_forge_get_avatar_requires_avatar_id():
    """smidja.forge_get_avatar must declare avatar_id as required."""
    ga = next(
        t for t in SMIDJA_TOOL_DEFINITIONS
        if t["function"]["name"] == "smidja.forge_get_avatar"
    )
    required = ga["function"]["parameters"].get("required", [])
    assert "avatar_id" in required
    props = ga["function"]["parameters"].get("properties", {})
    assert props["avatar_id"]["type"] == "string"


def test_forge_inspect_avatar_requires_avatar_id():
    """smidja.forge_inspect_avatar must declare avatar_id as required."""
    ia = next(
        t for t in SMIDJA_TOOL_DEFINITIONS
        if t["function"]["name"] == "smidja.forge_inspect_avatar"
    )
    required = ia["function"]["parameters"].get("required", [])
    assert "avatar_id" in required


def test_forge_tools_descriptions_mention_blender():
    """Forge tool descriptions must mention Blender or headless to set timing expectations."""
    forge_tools = [
        t for t in SMIDJA_TOOL_DEFINITIONS
        if t["function"]["name"].split(".", 1)[1].startswith("forge_")
    ]
    for tool in forge_tools:
        desc = tool["function"]["description"].lower()
        assert "blender" in desc or "headless" in desc or "slow" in desc, (
            f"Forge tool {tool['function']['name']!r} description does not mention "
            f"Blender, headless, or slow — caller needs timing expectation"
        )


def test_brunhand_tools_do_not_have_forge_prefix():
    """All Brúarhönd tools must NOT have actions starting with 'forge_'."""
    brunhand_tools = [
        t for t in SMIDJA_TOOL_DEFINITIONS
        if not t["function"]["name"].split(".", 1)[1].startswith("forge_")
    ]
    assert len(brunhand_tools) == 6
