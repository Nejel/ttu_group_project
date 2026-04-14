from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd


UNIFIED_REQUIRED_COLUMNS = [
    "job_title",
    "location",
    "sector",
    "salary_range",
    "industry",
    "job_description_skills",
]


@dataclass(frozen=True)
class DatasetSpec:
    source_name: str
    column_mapping: Mapping[str, str]
    file_path: Path | None = None
    required_targets: Sequence[str] = field(default_factory=lambda: tuple(UNIFIED_REQUIRED_COLUMNS))
    optional_targets: Sequence[str] = field(default_factory=tuple)
    extra_passthrough: Sequence[str] = field(default_factory=tuple)


DEFAULT_SPECS = [
    DatasetSpec(
        source_name="glassdoor_2023",
        file_path=Path("data/glassdoor_jobs_2023.csv"),
        column_mapping={
            "Job Title": "job_title",
            "Location": "location",
            "Sector": "sector",
            "Salary Estimate": "salary_range",
            "Industry": "industry",
            "Job Description": "job_description_skills",
        },
        extra_passthrough=[
            "Rating",
            "Company Name",
            "Size",
            "Founded",
            "Type of ownership",
            "Revenue",
        ],
    ),
    DatasetSpec(
        source_name="data_science_job_posts_2025",
        file_path=Path("data/data_science_job_posts_2025.csv"),
        column_mapping={
            "job_title": "job_title",
            "location": "location",
            "industry": "industry",
            "salary": "salary_range",
            "skills": "job_description_skills",
        },
        optional_targets=["sector"],
        extra_passthrough=[
            "seniority_level",
            "status",
            "company",
            "post_date",
            "headquarter",
            "ownership",
            "company_size",
            "revenue",
        ],
    ),
]

OUR_OWN_DATASET_DIR = Path("data/our_own_dataset")
OUR_OWN_DATASET_COLUMN_MAPPING = {
    "title": "job_title",
    "location": "location",
    "salary": "salary_range",
    "description": "job_description_skills",
}
OUR_OWN_DATASET_PASSTHROUGH_COLUMNS = (
    "company",
    "workType",
    "link",
    "source",
)


def _build_default_sources() -> list[DatasetSpec]:
    default_sources = list(DEFAULT_SPECS)

    for dataset_path in sorted(OUR_OWN_DATASET_DIR.glob("*.csv")):
        default_sources.append(
            DatasetSpec(
                source_name="our_own_dataset",
                file_path=dataset_path,
                column_mapping=OUR_OWN_DATASET_COLUMN_MAPPING,
                extra_passthrough=OUR_OWN_DATASET_PASSTHROUGH_COLUMNS,
            )
        )

    return default_sources


def _normalize_dataset(df: pd.DataFrame, spec: DatasetSpec) -> pd.DataFrame:
    normalized = pd.DataFrame(index=df.index)

    for source_col, target_col in spec.column_mapping.items():
        if source_col not in df.columns:
            continue
        normalized[target_col] = df[source_col]

    for target_col in spec.required_targets:
        if target_col not in normalized.columns:
            normalized[target_col] = pd.NA

    for target_col in spec.optional_targets:
        if target_col not in normalized.columns:
            normalized[target_col] = pd.NA

    normalized["source_dataset"] = spec.source_name

    for col in spec.extra_passthrough:
        normalized[col] = df[col] if col in df.columns else pd.NA

    passthrough_columns = [
        col
        for col in df.columns
        if col not in spec.column_mapping and col not in normalized.columns
    ]
    for col in passthrough_columns:
        normalized[col] = df[col]

    ordered_cols = [
        *UNIFIED_REQUIRED_COLUMNS,
        "source_dataset",
        *[col for col in normalized.columns if col not in UNIFIED_REQUIRED_COLUMNS and col != "source_dataset"],
    ]
    return normalized.loc[:, ordered_cols]


def build_unified_jobs_df(
    dataframes: list[pd.DataFrame] | None = None,
    sources: list[DatasetSpec] | None = None,
) -> pd.DataFrame:
    active_sources = sources if sources is not None else _build_default_sources()

    if not active_sources:
        raise ValueError("At least one dataset spec is required.")

    if dataframes is None:
        dataframes = []
        for source in active_sources:
            if source.file_path is None:
                raise ValueError(
                    "All dataset specs must define file_path when dataframes are not provided."
                )
            dataframes.append(pd.read_csv(source.file_path))

    if len(dataframes) != len(active_sources):
        raise ValueError("The number of dataframes must match the number of dataset specs.")

    normalized_frames = [
        _normalize_dataset(df=dataframe, spec=spec)
        for dataframe, spec in zip(dataframes, active_sources)
    ]

    unified_df = pd.concat(normalized_frames, ignore_index=True, sort=False)

    for col in UNIFIED_REQUIRED_COLUMNS:
        if col not in unified_df.columns:
            unified_df[col] = pd.NA

    ordered_cols = [
        *UNIFIED_REQUIRED_COLUMNS,
        "source_dataset",
        *[
            col
            for col in unified_df.columns
            if col not in UNIFIED_REQUIRED_COLUMNS and col != "source_dataset"
        ],
    ]
    return unified_df.loc[:, ordered_cols]
