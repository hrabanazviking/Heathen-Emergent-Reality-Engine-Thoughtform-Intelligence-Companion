"""
heretic.skilningr.senses — sense subpackage namespace.

Each sense lives in its own subpackage under senses/:
    senses/smidja/   — L5.5 Smiðja (Brúarhönd remote control)
    (future senses added as new subpackages per their milestones)

Each sense subpackage must export:
    - A sense class (e.g. SmidjaSense) with:
        - is_available property
        - async open() / async close()
        - async dispatch_tool_call(tool_call: dict) -> dict
        - tool_definitions property -> list[dict]
    - An INTERFACE.md describing the sense contract

Ref: docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle covenant)
"""
