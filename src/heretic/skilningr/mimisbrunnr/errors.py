"""
Mímisbrunnr error hierarchy — extending the Skilningr error tree.

All errors that cross the Mímisbrunnr boundary are subclasses of
SkilningrError so that callers who catch SkilningrError also catch
every Mímisbrunnr failure without needing a separate import.

Error taxonomy (v0.7 scaffold):

    SkilningrError
        LibraryError                    — root for all Mímisbrunnr failures
            LibraryDownloadError        — network-layer download failure
            IntegrityError              — SHA-256 mismatch on a downloaded source
            ManifestError               — manifest is corrupt, missing, or invalid
            ConsentRefused              — operator declined the download prompt
            LibraryIndexError           — keyword index build or search failure

Design rule: these errors are NEVER propagated to the agent as Python
exceptions. The LibrarySense dispatch boundary catches them and
translates them into structured tool_result error dicts per
SENSE_CONTRACTS.md §3.

Ref: src/heretic/skilningr/errors.py (SkilningrError — root class)
     src/heretic/skilningr/mimisbrunnr/INTERFACE.md
     docs/architecture/SENSE_CONTRACTS.md §3 Error Taxonomy
"""

from __future__ import annotations

from heretic.skilningr.errors import SkilningrError


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

class LibraryError(SkilningrError):
    """Root error for the Mímisbrunnr library subsystem and the Library sense.

    All errors raised within mimisbrunnr/ are subclasses of this.
    Callers catching SkilningrError also catch LibraryError and its
    subclasses. All LibraryError subclasses are caught at the
    LibrarySense dispatch boundary and translated into structured
    tool_result error dicts — they are never re-raised to L1 Bifröst.

    Corresponds to SENSE_CONTRACTS.md sense: "library".
    """


# ---------------------------------------------------------------------------
# Specific failure modes
# ---------------------------------------------------------------------------

class LibraryDownloadError(LibraryError):
    """A network-layer failure occurred while downloading a LibrarySource.

    Covers DNS failure, TCP refused, TLS error, HTTP non-200 status,
    and any transport error from httpx. The source_id and URL are
    available in the error message.

    Forge should translate this to SENSE_CONTRACTS.md code
    EXTERNAL_APP_UNAVAILABLE.
    """


class IntegrityError(LibraryError):
    """The downloaded file's SHA-256 hash does not match the expected hash
    stored in the manifest.

    The downloaded file is NOT written to the permanent store when this
    error is raised — no corrupt content is persisted.

    Forge should translate this to SENSE_CONTRACTS.md code
    SENSE_INTERNAL_ERROR with a message that includes the source_id,
    expected hash, and actual hash.
    """


class ManifestError(LibraryError):
    """The Mímisbrunnr manifest is corrupt, structurally invalid, or
    missing a required field.

    Raised by NorseStarterPackManifest construction or local manifest
    loading when the data does not conform to the expected schema.

    Forge should translate this to SENSE_CONTRACTS.md code
    SENSE_INTERNAL_ERROR.
    """


class ConsentRefused(LibraryError):
    """The operator declined the download consent prompt.

    Raised by prompt_for_download() when the operator answers 'no'
    (or auto_yes=False and the prompt receives no affirmative reply).
    No download is attempted after this is raised.

    Forge should translate this to SENSE_CONTRACTS.md code
    PERMISSION_DENIED.
    """


class LibraryIndexError(LibraryError):
    """A keyword index build or search operation failed.

    Raised by KeywordIndex.build() when the source data is missing or
    corrupt, and by KeywordIndex.search() when the index has not been
    built or the search cannot complete.

    Forge should translate this to SENSE_CONTRACTS.md code
    SENSE_INTERNAL_ERROR.
    """
