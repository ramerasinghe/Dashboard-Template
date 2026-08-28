import pandas as pd

REQUIRED_COLUMNS = [
    "2-Week Mark",
    "Days Left",
    "RRD",
    "Score",
    "Application",
    "Environment",
    "App ID",
    "Host",
    "Server Type",
    "Scheduling",
    "Scanner Location",
    "Title",
    "Tracking ID",
    "QID",
    "ATC",
    "Primary?",
    "Intrusive?",
    "Patch Available?",
    "Cluster Group",
]

DEFAULT_DISPLAY_COLUMNS = [
    "Tracking ID",
    "QID",
    "Title",
    "Score",
    "Application",
    "ATC",
    "Host",
    "Environment",
    "Server Type",
    "2-Week Mark",
    "Calculated Days Left",
    "RRD",
    "Due Bucket",
    "Operational Priority",
    "Scheduling",
    "Intrusive?",
    "Patch Available?",
    "Cluster Group",
]

YES_VALUES = {"yes", "y", "true", "1"}

def _normalize_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()

def _is_yes(series: pd.Series) -> pd.Series:
    return (
        _normalize_text(series)
        .str.lower()
        .isin(YES_VALUES)
    )

def prepare_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and derive dashboard fields while preserving all original source columns.

    Business definitions:
    - RRD = final remediation date.
    - 2-Week Mark = operational due date; expected to equal RRD - 14 days.
    - ATC = Application Technical Contact.
    - Calculated Days Left = 2-Week Mark - today.
    """
    df = raw_df.copy()

    for col in ["2-Week Mark", "RRD"]:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.normalize()

    for col in ["Score", "Days Left"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_columns = [
        "Application", "Environment", "App ID", "Host", "Server Type",
        "Scheduling", "Scanner Location", "Title", "Tracking ID",
        "QID", "ATC", "Primary?", "Intrusive?", "Patch Available?",
        "Cluster Group"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = _normalize_text(df[col])

    today = pd.Timestamp.today().normalize()

    df["Calculated Days Left"] = (
        df["2-Week Mark"] - today
    ).dt.days.astype("Int64")

    df["Overdue"] = df["Calculated Days Left"].lt(0)

    def due_bucket(days):
        if pd.isna(days):
            return "Unknown"
        if days < 0:
            return "Overdue"
        if days <= 7:
            return "Due Within 7 Days"
        if days <= 14:
            return "Due Within 14 Days"
        if days <= 30:
            return "Due Within 30 Days"
        return "On Track"

    df["Due Bucket"] = df["Calculated Days Left"].apply(due_bucket)

    df["High Score"] = df["Score"].ge(7.0)
    df["Intrusive Flag"] = _is_yes(df["Intrusive?"])
    df["Patch Available Flag"] = _is_yes(df["Patch Available?"])

    # Priority is intentionally operational rather than a replacement for VVMS severity.
    def operational_priority(row):
        days = row["Calculated Days Left"]
        score = row["Score"]
        intrusive = row["Intrusive Flag"]
        patch = row["Patch Available Flag"]

        if pd.isna(days):
            return "Review Date"
        if days < 0:
            return "Immediate Attention"
        if days <= 7 and score >= 7:
            return "Immediate Attention"
        if days <= 14 and intrusive:
            return "Coordination Required"
        if days <= 14 and patch:
            return "Patch / Remediate"
        if days <= 14:
            return "Due Soon"
        if days <= 30:
            return "Plan Remediation"
        return "On Track"

    df["Operational Priority"] = df.apply(
        operational_priority,
        axis=1,
    )

    priority_rank = {
        "Immediate Attention": 1,
        "Coordination Required": 2,
        "Patch / Remediate": 3,
        "Due Soon": 4,
        "Plan Remediation": 5,
        "Review Date": 6,
        "On Track": 7,
    }

    df["Operational Priority Rank"] = (
        df["Operational Priority"]
        .map(priority_rank)
        .fillna(99)
    )

    # Data quality checks
    df["Expected 2-Week Mark"] = df["RRD"] - pd.Timedelta(days=14)
    df["Deadline Date Difference"] = (
        df["2-Week Mark"] - df["Expected 2-Week Mark"]
    ).dt.days.astype("Int64")

    df["Days Left Difference"] = (
        df["Days Left"] - df["Calculated Days Left"]
    ).astype("Float64")

    return df

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df.copy()

    search_text = (filters.get("search_text") or "").strip().lower()
    if search_text:
        search_cols = [
            "Tracking ID", "QID", "Title",
            "Application", "ATC", "Host", "App ID",
        ]
        mask = pd.Series(False, index=out.index)
        for col in search_cols:
            mask = mask | out[col].fillna("").astype(str).str.lower().str.contains(
                search_text,
                regex=False,
            )
        out = out[mask]

    categorical_filters = [
        "Application",
        "Environment",
        "ATC",
        "Server Type",
        "Cluster Group",
        "Due Bucket",
        "Intrusive?",
        "Patch Available?",
    ]

    for col in categorical_filters:
        selected = filters.get(col) or []
        if selected:
            out = out[out[col].astype(str).isin([str(x) for x in selected])]

    score_range = filters.get("score_range")
    if score_range:
        lo, hi = score_range
        out = out[out["Score"].between(lo, hi, inclusive="both")]

    return out

def metric_counts(df: pd.DataFrame) -> dict:
    days = df["Calculated Days Left"]

    return {
        "total": len(df),
        "overdue": int(days.lt(0).sum()),
        "due_7": int(days.between(0, 7, inclusive="both").sum()),
        "due_14": int(days.between(0, 14, inclusive="both").sum()),
        "high_score": int(df["Score"].ge(7.0).sum()),
        "patch_available": int(df["Patch Available Flag"].sum()),
        "intrusive": int(df["Intrusive Flag"].sum()),
        "applications": int(df["Application"].nunique(dropna=True)),
        "atcs": int(df["ATC"].replace("", pd.NA).nunique(dropna=True)),
    }
