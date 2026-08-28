import io
import pandas as pd
import streamlit as st

from data_model import (
    REQUIRED_COLUMNS,
    prepare_data,
    apply_filters,
    metric_counts,
    DEFAULT_DISPLAY_COLUMNS,
)

st.set_page_config(
    page_title="Vulnerability Alert Management",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Vulnerability Alert Management")
st.caption(
    "Interactive remediation dashboard for vulnerability management and application technical contacts (ATCs). "
    "The operational due date is the 2-Week Mark, which is 14 days before the RRD."
)

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload VVMS CSV", type=["csv"])
    st.caption("Use the included sample_vvms.csv to test the dashboard.")

@st.cache_data
def load_uploaded(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))

@st.cache_data
def load_sample() -> pd.DataFrame:
    return pd.read_csv("sample_vvms.csv")

if uploaded is not None:
    raw_df = load_uploaded(uploaded.getvalue())
    source_label = uploaded.name
else:
    raw_df = load_sample()
    source_label = "sample_vvms.csv"

missing = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
if missing:
    st.error("The uploaded CSV is missing required columns:")
    st.code("\n".join(missing))
    st.stop()

df = prepare_data(raw_df)

with st.sidebar:
    st.divider()
    st.header("Filters")

    search_text = st.text_input(
        "Search",
        placeholder="Tracking ID, QID, title, host, application..."
    )

    application = st.multiselect(
        "Application",
        sorted(df["Application"].dropna().astype(str).unique())
    )

    environment = st.multiselect(
        "Environment",
        sorted(df["Environment"].dropna().astype(str).unique())
    )

    atc = st.multiselect(
        "ATC",
        sorted(df["ATC"].dropna().astype(str).unique())
    )

    server_type = st.multiselect(
        "Server Type",
        sorted(df["Server Type"].dropna().astype(str).unique())
    )

    cluster = st.multiselect(
        "Cluster Group",
        sorted(df["Cluster Group"].dropna().astype(str).unique())
    )

    due_bucket = st.multiselect(
        "Due Status",
        ["Overdue", "Due Within 7 Days", "Due Within 14 Days",
         "Due Within 30 Days", "On Track", "Unknown"]
    )

    intrusive = st.multiselect(
        "Intrusive?",
        sorted(df["Intrusive?"].dropna().astype(str).unique())
    )

    patch_available = st.multiselect(
        "Patch Available?",
        sorted(df["Patch Available?"].dropna().astype(str).unique())
    )

    score_min = float(df["Score"].min()) if df["Score"].notna().any() else 0.0
    score_max = float(df["Score"].max()) if df["Score"].notna().any() else 10.0
    score_range = st.slider(
        "Score range",
        min_value=float(np.floor(score_min)),
        max_value=float(np.ceil(score_max)),
        value=(float(np.floor(score_min)), float(np.ceil(score_max))),
        step=0.1,
    )

filters = {
    "search_text": search_text,
    "Application": application,
    "Environment": environment,
    "ATC": atc,
    "Server Type": server_type,
    "Cluster Group": cluster,
    "Due Bucket": due_bucket,
    "Intrusive?": intrusive,
    "Patch Available?": patch_available,
    "score_range": score_range,
}

filtered = apply_filters(df, filters)
counts = metric_counts(filtered)

st.caption(f"Source: **{source_label}** · Showing **{len(filtered):,} of {len(df):,}** findings")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Findings", f"{counts['total']:,}")
k2.metric("Overdue", f"{counts['overdue']:,}")
k3.metric("Due ≤ 7 Days", f"{counts['due_7']:,}")
k4.metric("Due ≤ 14 Days", f"{counts['due_14']:,}")
k5.metric("High Score ≥ 7", f"{counts['high_score']:,}")

k6, k7, k8, k9 = st.columns(4)
k6.metric("Patch Available", f"{counts['patch_available']:,}")
k7.metric("Intrusive", f"{counts['intrusive']:,}")
k8.metric("Applications", f"{counts['applications']:,}")
k9.metric("ATCs", f"{counts['atcs']:,}")

tab1, tab2, tab3 = st.tabs(
    ["📊 Dashboard", "📋 Findings Workspace", "✅ Data Quality"]
)

with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Remediation urgency")
        urgency_order = [
            "Overdue",
            "Due Within 7 Days",
            "Due Within 14 Days",
            "Due Within 30 Days",
            "On Track",
            "Unknown",
        ]
        urgency = (
            filtered["Due Bucket"]
            .value_counts()
            .reindex(urgency_order, fill_value=0)
            .rename_axis("Due Bucket")
            .to_frame("Findings")
        )
        st.bar_chart(urgency)

    with c2:
        st.subheader("Findings by application")
        app_counts = (
            filtered["Application"]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
            .head(12)
            .rename_axis("Application")
            .to_frame("Findings")
        )
        st.bar_chart(app_counts)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Findings by environment")
        env_counts = (
            filtered["Environment"]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
            .rename_axis("Environment")
            .to_frame("Findings")
        )
        st.bar_chart(env_counts)

    with c4:
        st.subheader("Findings by ATC")
        atc_counts = (
            filtered["ATC"]
            .fillna("Unassigned")
            .astype(str)
            .value_counts()
            .head(12)
            .rename_axis("ATC")
            .to_frame("Findings")
        )
        st.bar_chart(atc_counts)

    st.subheader("Priority remediation queue")
    priority_df = (
        filtered.sort_values(
            ["Operational Priority Rank", "Calculated Days Left", "Score"],
            ascending=[True, True, False],
            na_position="last",
        )
        .head(20)
    )

    st.dataframe(
        priority_df[
            [
                "Tracking ID", "QID", "Title", "Score",
                "Application", "ATC", "Host",
                "2-Week Mark", "Calculated Days Left",
                "RRD", "Operational Priority",
                "Intrusive?", "Patch Available?", "Scheduling"
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "2-Week Mark": st.column_config.DateColumn("2-Week Mark"),
            "RRD": st.column_config.DateColumn("RRD"),
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
            "Calculated Days Left": st.column_config.NumberColumn("Days Left"),
        },
    )

with tab2:
    st.subheader("Findings Workspace")
    st.caption(
        "Spreadsheet-style view using the same filters as the dashboard. "
        "Sort columns by clicking headers and select a row to inspect the finding."
    )

    show_all_columns = st.toggle("Show all CSV columns", value=False)

    if show_all_columns:
        table_df = filtered.copy()
    else:
        table_df = filtered[DEFAULT_DISPLAY_COLUMNS].copy()

    table_df = table_df.sort_values(
        ["Operational Priority Rank", "Calculated Days Left", "Score"],
        ascending=[True, True, False],
        na_position="last",
    )

    selection = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=520,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "2-Week Mark": st.column_config.DateColumn("2-Week Mark"),
            "RRD": st.column_config.DateColumn("RRD"),
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
            "Calculated Days Left": st.column_config.NumberColumn("Days Left"),
        },
    )

    if selection.selection.rows:
        selected_position = selection.selection.rows[0]
        selected_row = table_df.iloc[selected_position]

        st.subheader("Selected finding")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Tracking ID", str(selected_row.get("Tracking ID", "")))
        d2.metric("Score", f"{selected_row.get('Score', 0):.1f}")
        d3.metric("Days Left", str(selected_row.get("Calculated Days Left", "")))
        d4.metric("Priority", str(selected_row.get("Operational Priority", "")))

        detail_cols = [
            "QID", "Title", "Application", "App ID", "ATC", "Host",
            "Environment", "Server Type", "Cluster Group", "2-Week Mark",
            "RRD", "Scheduling", "Scanner Location", "Primary?",
            "Intrusive?", "Patch Available?"
        ]
        details = pd.DataFrame(
            {
                "Field": detail_cols,
                "Value": [selected_row.get(c, "") for c in detail_cols],
            }
        )
        st.dataframe(details, use_container_width=True, hide_index=True)

    export_df = filtered.drop(
        columns=["Operational Priority Rank"],
        errors="ignore",
    ).copy()

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download filtered CSV",
        data=csv_bytes,
        file_name="filtered_vulnerability_findings.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Data Quality / Validation")

    dq1, dq2, dq3 = st.columns(3)
    dq1.metric(
        "Missing 2-Week Mark",
        int(df["2-Week Mark"].isna().sum())
    )
    dq2.metric(
        "Missing RRD",
        int(df["RRD"].isna().sum())
    )
    dq3.metric(
        "Missing ATC",
        int(df["ATC"].isna().sum() | (df["ATC"].astype(str).str.strip() == ""))
    )

    st.markdown("**Deadline consistency**")
    st.caption(
        "The expected 2-Week Mark is RRD minus 14 calendar days. "
        "Rows below do not match that relationship."
    )

    mismatched_dates = df[
        df["Deadline Date Difference"].notna()
        & (df["Deadline Date Difference"] != 0)
    ]

    st.dataframe(
        mismatched_dates[
            [
                "Tracking ID", "Application", "ATC",
                "2-Week Mark", "Expected 2-Week Mark",
                "RRD", "Deadline Date Difference"
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    if "Days Left" in df.columns:
        st.markdown("**VVMS Days Left vs calculated Days Left**")
        st.caption(
            "Calculated Days Left is based on today's date and the 2-Week Mark."
        )

        discrepancy = df[
            df["Days Left Difference"].notna()
            & (df["Days Left Difference"] != 0)
        ]

        st.dataframe(
            discrepancy[
                [
                    "Tracking ID", "2-Week Mark",
                    "Days Left", "Calculated Days Left",
                    "Days Left Difference"
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
