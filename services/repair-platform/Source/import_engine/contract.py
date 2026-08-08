"""Machine-readable v1.0 Service Type import-readiness contract."""

from __future__ import annotations

from dataclasses import dataclass

CONTRACT_VERSION = "0.1"
APPROVED_VERSION = "v1.0"
APPROVED_SHA256 = (
    "DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA"
)
SVC000343 = "SVC000343"

RECOGNIZED_STATUSES = frozenset(
    {
        "Approved",
        "Archived",
        "Pending Review",
        "Pending Service Review",
        "Pending Labor Review",
        "Pending Evidence Review",
        "Ready for Approval",
        "Rejected",
        "Unresolved",
    }
)


@dataclass(frozen=True, slots=True)
class WorksheetContract:
    """Exact worksheet/table contract for an approved release."""

    worksheet: str
    table: str
    headers: tuple[str, ...]
    expected_rows: int
    status_field: str | None = None
    expected_status_counts: tuple[tuple[str, int], ...] = ()
    import_target: str | None = None
    key_field: str | None = None


WORKSHEET_CONTRACTS = (
    WorksheetContract(
        "00 - Instructions",
        "tblSTNInstructions",
        (
            "Topic",
            "Guidance",
            "Alias Rule Type",
            "Mapping Method",
            "Confidence",
            "Review Status",
            "Device Family Code",
            "Manufacturer ID",
            "Labor Standard ID",
            "Yes/No Value",
            "DeviceFamilyID",
            "Manufacturer ID2",
        ),
        265,
    ),
    WorksheetContract(
        "01 - Canonical Service Types",
        "tblCanonicalServiceTypes",
        (
            "Proposed Canonical Service Type ID",
            "Service Category",
            "Service Type",
            "Service Description",
            "Applies To",
            "Estimated Time (Min)",
            "Default Warranty (Days)",
            "Taxable",
            "Active",
            "Internal Notes",
            "Identity Authority",
            "Review Status",
            "Reviewer Notes",
        ),
        77,
        "Review Status",
        (("Pending Review", 77),),
        "shadow_canonical_service_types",
        "Proposed Canonical Service Type ID",
    ),
    WorksheetContract(
        "02 - Service Type Aliases",
        "tblServiceTypeAliases",
        (
            "Alias ID",
            "Source System",
            "Source Field",
            "Source Value",
            "Normalized Source Value",
            "Proposed Canonical Service Type ID",
            "Proposed Canonical Service Type",
            "Alias Rule Type",
            "Evidence",
            "Confidence",
            "Review Status",
            "Reviewer",
            "Reviewer Notes",
        ),
        17,
        "Review Status",
        (("Ready for Approval", 17),),
        "shadow_service_type_aliases",
        "Alias ID",
    ),
    WorksheetContract(
        "03 - Service Normalization",
        "tblServiceNormalization",
        (
            "Service ID",
            "Service Name",
            "Current Repair Type ID",
            "Current Repair Type",
            "Manufacturer ID",
            "Manufacturer Name",
            "Device Family Code",
            "Device Family Name",
            "Proposed Canonical Service Type ID",
            "Proposed Canonical Service Type",
            "Mapping Method",
            "Mapping Evidence",
            "Confidence",
            "Review Status",
            "Reviewer Notes",
        ),
        313,
        "Review Status",
        (("Pending Labor Review", 313),),
        "shadow_service_normalization",
        "Service ID",
    ),
    WorksheetContract(
        "04 - Labor Normalization",
        "tblLaborNormalization",
        (
            "Labor Standard ID",
            "Legacy Labor ID",
            "Labor Name",
            "Current Repair Type",
            "Device Family Code",
            "Device Family",
            "Manufacturer ID",
            "Manufacturer",
            "Proposed Canonical Service Type ID",
            "Proposed Canonical Service Type",
            "Mapping Method",
            "Mapping Evidence",
            "Confidence",
            "Review Status",
            "Reviewer Notes",
        ),
        265,
        "Review Status",
        (
            ("Pending Evidence Review", 167),
            ("Pending Labor Review", 11),
            ("Pending Review", 85),
            ("Unresolved", 2),
        ),
        "shadow_labor_normalization",
        "Labor Standard ID",
    ),
    WorksheetContract(
        "05 - Service Labor Candidates",
        "tblServiceLaborCandidates",
        (
            "Service ID",
            "Service Name",
            "Canonical Service Type ID",
            "Canonical Service Type",
            "Device Family Code",
            "Manufacturer ID",
            "Suggested Labor Standard ID",
            "Legacy Labor ID",
            "Labor Name",
            "Standard Minutes",
            "Minimum Minutes",
            "Maximum Minutes",
            "Candidate Method",
            "Evidence",
            "Confidence",
            "Ambiguity Count",
            "Review Status",
            "Reviewer Notes",
        ),
        0,
        "Review Status",
    ),
    WorksheetContract(
        "06 - Unresolved Review",
        "tblSTNUnresolvedReview",
        (
            "Record Type",
            "Source Record ID",
            "Source Name",
            "Current Type",
            "Candidate Canonical Types",
            "Candidate Labor Standards",
            "Ambiguity Reason",
            "Missing Evidence",
            "Required Action",
            "Review Priority",
            "Review Status",
            "Reviewer Notes",
        ),
        147,
        "Review Status",
        (("Pending Evidence Review", 147),),
    ),
    WorksheetContract(
        "07 - Validation Summary",
        "tblSTNValidationSummary",
        ("Validation", "Result", "Count"),
        8,
    ),
    WorksheetContract(
        "08 - Revision History",
        "tblSTNRevisionHistory",
        ("Version", "Date", "Change", "Status"),
        2,
        "Status",
        (("Pending Review", 2),),
    ),
    WorksheetContract(
        "09 - Import Metadata",
        "tblSTNImportMetadata",
        ("Metadata Field", "Value"),
        26,
    ),
)

WORKSHEET_BY_NAME = {
    contract.worksheet: contract for contract in WORKSHEET_CONTRACTS
}
IMPORTABLE_WORKSHEETS = tuple(
    contract for contract in WORKSHEET_CONTRACTS if contract.import_target
)
