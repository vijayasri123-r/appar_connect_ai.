#streamlit run app.py
import streamlit as st
import pandas as pd
import sqlite3
import re
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

# =====================================================
# APAAR CONNECT AI
# Student Data Management & Verification Prototype
# =====================================================

st.set_page_config(
    page_title="APAAR Connect AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = Path(__file__).with_name("apaar_connect.db")

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f5f7ff, #edf5ff);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101c44, #273c75);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    padding: 28px;
    border-radius: 20px;
    color: white;
    background: linear-gradient(120deg, #283c86, #45a247);
    margin-bottom: 20px;
}

.hero h1 {
    font-size: 34px;
    margin-bottom: 8px;
}

.hero p {
    font-size: 16px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    border-left: 5px solid #4659d5;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.06);
    margin-bottom: 12px;
}

.metric-title {
    font-size: 14px;
    color: #555;
}

.metric-value {
    font-size: 29px;
    font-weight: bold;
    color: #202c65;
}

.section-title {
    color: #243b80;
    font-size: 23px;
    font-weight: bold;
}

.small-note {
    font-size: 13px;
    color: #555;
}

.stButton button {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE
# =====================================================

def init_db():
    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action TEXT,
            details TEXT
        )
        """)


def log_action(action, details):
    # Prototype audit log.
    # Production systems need access-controlled,
    # tamper-resistant audit logging.

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        INSERT INTO audit_logs
        (timestamp, action, details)
        VALUES (?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            action,
            details
        ))


init_db()


# =====================================================
# SAMPLE DATA
# =====================================================

def create_sample_data():

    data = {
        "Student_ID": [
            "STU001",
            "STU002",
            "STU003",
            "STU004",
            "STU005",
            "STU006",
            "STU007",
            "STU008"
        ],

        "APAAR_ID": [
            "123456789012",
            "234567890123",
            "345678901234",
            "123456789012",
            "INVALID",
            "",
            "567890123456",
            "678901234567"
        ],

        "Student_Name": [
            "Student A",
            "Student B",
            "Student C",
            "Student D",
            "Student E",
            "Student F",
            "Student G",
            "Student H"
        ],

        "Programme": [
            "B.E. ECE",
            "B.E. CSE",
            "B.E. ECE",
            "B.E. ECE",
            "B.E. CSE",
            "B.E. EEE",
            "B.E. ECE",
            "B.E. CSE"
        ],

        "Admission_Year": [
            2026, 2026, 2026, 2026,
            2026, 2026, 2026, 2026
        ],

        "Category": [
            "Regular",
            "Regular",
            "NRI",
            "Regular",
            "Regular",
            "Regular",
            "OCI",
            "Regular"
        ]
    }

    return pd.DataFrame(data)


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.markdown("## 🎓 APAAR CONNECT AI")
st.sidebar.caption("Student Verification Platform")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "🏠 Dashboard",
        "📤 Upload Student Data",
        "🔍 Validation Centre",
        "👨‍🎓 Student Records",
        "📊 Analytics",
        "🕒 Audit History",
        "⚙️ Settings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Prototype Mode\n\n"
    "Use synthetic student data only."
)


# =====================================================
# SESSION STATE
# =====================================================

if "student_data" not in st.session_state:
    st.session_state.student_data = create_sample_data()

if "approved_intake" not in st.session_state:
    st.session_state.approved_intake = 120

if "institution_name" not in st.session_state:
    st.session_state.institution_name = "Demo Engineering Institution"

if "institution_id" not in st.session_state:
    st.session_state.institution_id = "DEMO001"


# =====================================================
# HELPERS
# =====================================================

REQUIRED_COLUMNS = [
    "Student_ID",
    "APAAR_ID",
    "Student_Name",
    "Programme",
    "Admission_Year",
    "Category"
]


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def safe_display_id(value):
    """
    Mask identifier in the UI.
    The raw value should not be displayed.
    """

    value = clean_text(value)

    if not value:
        return "Missing"

    if len(value) <= 4:
        return "****"

    return "*" * (len(value) - 4) + value[-4:]


def valid_apaar_format(value):
    """
    Illustrative prototype format check only.
    A 12-digit pattern does NOT establish
    APAAR authenticity or ownership.
    """

    value = clean_text(value)

    return bool(re.fullmatch(r"\d{12}", value))


def prepare_dataframe(df):

    df = df.copy()

    # Normalize column names
    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # Required column check
    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        return None, missing_columns

    df = df[REQUIRED_COLUMNS].copy()

    # Normalize text
    for col in [
        "Student_ID",
        "APAAR_ID",
        "Student_Name",
        "Programme",
        "Category"
    ]:
        df[col] = df[col].apply(clean_text)

    # Normalize admission year
    df["Admission_Year"] = pd.to_numeric(
        df["Admission_Year"],
        errors="coerce"
    )

    return df, []


def validate_data(df):

    result = df.copy()

    result["Issues"] = ""
    result["Review_Status"] = "Review Required"

    # Empty identifiers
    result["Student_ID"] = result["Student_ID"].fillna("")
    result["APAAR_ID"] = result["APAAR_ID"].fillna("")

    # Duplicate Student IDs
    duplicate_student = (
        result["Student_ID"].ne("") &
        result["Student_ID"].duplicated(keep=False)
    )

    # Duplicate APAAR IDs
    valid_id_mask = result["APAAR_ID"].apply(
        valid_apaar_format
    )

    duplicate_apaar = (
        valid_id_mask &
        result["APAAR_ID"].duplicated(keep=False)
    )

    for idx, row in result.iterrows():

        issues = []

        student_id = clean_text(row["Student_ID"])
        apaar_id = clean_text(row["APAAR_ID"])
        student_name = clean_text(row["Student_Name"])
        programme = clean_text(row["Programme"])
        category = clean_text(row["Category"])
        admission_year = row["Admission_Year"]

        if not student_id:
            issues.append("Missing Student ID")

        if not student_name:
            issues.append("Missing Student Name")

        if not programme:
            issues.append("Missing Programme")

        if not category:
            issues.append("Missing Category")

        if not apaar_id:
            issues.append("Missing APAAR ID")

        elif not valid_apaar_format(apaar_id):
            issues.append("Invalid APAAR ID format")

        if duplicate_student.loc[idx]:
            issues.append("Duplicate Student ID")

        if duplicate_apaar.loc[idx]:
            issues.append("Duplicate APAAR ID")

        if pd.isna(admission_year):
            issues.append("Missing/Invalid Admission Year")

        elif (
            admission_year < 2000 or
            admission_year > datetime.now().year + 1 or
            admission_year % 1 != 0
        ):
            issues.append("Admission Year requires review")

        result.at[idx, "Issues"] = (
            "; ".join(issues) if issues
            else "No basic validation issues detected"
        )

        if issues:
            result.at[idx, "Review_Status"] = "Review Required"
        else:
            result.at[idx, "Review_Status"] = "Format Checks Passed"

    return result


# =====================================================
# HEADER
# =====================================================

def show_header(title, subtitle):

    st.markdown(f"""
    <div class="hero">
        <h1>🎓 {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# CURRENT DATA
# =====================================================

raw_data = st.session_state.student_data

validated_data = validate_data(raw_data)

total_students = len(raw_data)

valid_format_count = (
    raw_data["APAAR_ID"].apply(valid_apaar_format).sum()
)

missing_apaar_count = (
    raw_data["APAAR_ID"].apply(
        lambda x: clean_text(x) == ""
    ).sum()
)

duplicate_apaar_count = (
    raw_data.loc[
        raw_data["APAAR_ID"].apply(valid_apaar_format),
        "APAAR_ID"
    ].duplicated(keep=False).sum()
)

issue_count = (
    validated_data["Review_Status"]
    .eq("Review Required")
    .sum()
)


# =====================================================
# DASHBOARD
# =====================================================

if page == "🏠 Dashboard":

    show_header(
        "APAAR Connect AI",
        "Smart Student Data Management & Verification Dashboard"
    )

    st.caption(
        "Demo environment | Synthetic records | "
        "No official APAAR verification performed"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👨‍🎓 Total Students</div>
            <div class="metric-value">{total_students}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🪪 Format-Passing IDs</div>
            <div class="metric-value">{valid_format_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⚠️ Records Requiring Review</div>
            <div class="metric-value">{issue_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔁 Duplicate ID Rows</div>
            <div class="metric-value">{duplicate_apaar_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    left, right = st.columns(2)

    with left:

        st.subheader("🏫 Institution Overview")

        st.info(
            f"Institution: {st.session_state.institution_name}"
        )

        st.write(
            f"**Institution ID:** "
            f"{st.session_state.institution_id}"
        )

        st.write(
            f"**Configured Approved Intake:** "
            f"{st.session_state.approved_intake}"
        )

        st.write(
            f"**Reported Student Records:** {total_students}"
        )

        st.write(
            f"**Missing APAAR IDs:** {missing_apaar_count}"
        )

    with right:

        st.subheader("📊 Enrolment Monitoring")

        intake = st.session_state.approved_intake

        if intake > 0:

            enrolment_ratio = total_students / intake

            st.progress(
                min(enrolment_ratio, 1.0)
            )

            st.write(
                f"Reported records: {total_students}/{intake}"
            )

            if total_students > intake:
                st.warning(
                    "Reported records exceed configured intake. "
                    "Review applicable seat rules and categories."
                )
            else:
                st.success(
                    "Reported records do not exceed "
                    "the configured intake."
                )

        else:
            st.warning("Configure approved intake in Settings.")

    st.markdown("---")

    st.subheader("🚨 Recent Validation Findings")

    display = validated_data[
        validated_data["Review_Status"] == "Review Required"
    ].copy()

    if not display.empty:

        display["APAAR_ID"] = display["APAAR_ID"].apply(
            safe_display_id
        )

        st.dataframe(
            display[
                [
                    "Student_ID",
                    "APAAR_ID",
                    "Programme",
                    "Issues"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("No basic validation issues detected.")


# =====================================================
# UPLOAD STUDENT DATA
# =====================================================

elif page == "📤 Upload Student Data":

    show_header(
        "Student Data Upload",
        "Upload and validate institution student records"
    )

    st.warning(
        "Use synthetic data only. "
        "Do not upload real APAAR IDs or personal student records "
        "into this demonstration."
    )

    st.subheader("📥 Download Sample CSV")

    sample = create_sample_data()

    # Demo values only
    sample_csv = sample.to_csv(index=False)

    st.download_button(
        "⬇️ Download Sample Student CSV",
        data=sample_csv,
        file_name="sample_students.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("📤 Upload Student CSV")

    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=["csv"]
    )

    if uploaded_file:

        try:

            df = pd.read_csv(
                uploaded_file,
                dtype=str,
                keep_default_na=False
            )

            st.write("### Uploaded Preview")

            st.dataframe(
                df.head(10),
                use_container_width=True
            )

            if st.button(
                "🔍 Validate and Load Records",
                type="primary"
            ):

                prepared, missing_cols = prepare_dataframe(df)

                if missing_cols:

                    st.error(
                        "Missing columns: " +
                        ", ".join(missing_cols)
                    )

                elif prepared.empty:

                    st.error("The uploaded CSV contains no records.")

                elif len(prepared) > 10000:

                    st.error(
                        "Prototype limit: 10,000 records per upload."
                    )

                else:

                    st.session_state.student_data = prepared

                    # Do not store raw APAAR IDs in audit logs
                    log_action(
                        "DATA_UPLOAD",
                        json.dumps({
                            "record_count": len(prepared),
                            "source": "CSV"
                        })
                    )

                    st.success(
                        f"{len(prepared)} records loaded successfully!"
                    )

                    st.info(
                        "Go to Validation Centre to inspect results."
                    )

        except Exception:

            st.error(
                "Unable to read this CSV. "
                "Please check the file format."
            )


# =====================================================
# VALIDATION CENTRE
# =====================================================

elif page == "🔍 Validation Centre":

    show_header(
        "Validation Centre",
        "Identify missing information and possible inconsistencies"
    )

    st.info(
        "These are preliminary checks. "
        "A passed result is not official verification."
    )

    df = validate_data(
        st.session_state.student_data
    )

    st.subheader("📋 Validation Summary")

    a, b, c = st.columns(3)

    a.metric(
        "Total Records",
        len(df)
    )

    b.metric(
        "Review Required",
        (df["Review_Status"] == "Review Required").sum()
    )

    c.metric(
        "Format Checks Passed",
        (df["Review_Status"] == "Format Checks Passed").sum()
    )

    st.markdown("---")

    st.subheader("🔎 Filter Records")

    filter_option = st.selectbox(
        "Select Status",
        [
            "All Records",
            "Review Required",
            "Format Checks Passed"
        ]
    )

    if filter_option != "All Records":

        df = df[
            df["Review_Status"] == filter_option
        ]

    # Mask identifiers
    df = df.copy()

    df["APAAR_ID"] = df["APAAR_ID"].apply(
        safe_display_id
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    st.subheader("📥 Export Validation Report")

    report = validate_data(
        st.session_state.student_data
    ).copy()

    # Mask student identifiers for exported report
    report["APAAR_ID"] = report["APAAR_ID"].apply(
        safe_display_id
    )

    report_csv = report.to_csv(index=False)

    st.download_button(
        "Download Validation Report",
        data=report_csv,
        file_name="validation_report.csv",
        mime="text/csv"
    )

    if st.button("📝 Record Validation Event"):

        log_action(
            "VALIDATION_RUN",
            json.dumps({
                "records_checked": len(report),
                "records_requiring_review": int(
                    (
                        report["Review_Status"]
                        == "Review Required"
                    ).sum()
                )
            })
        )

        st.success("Validation event recorded.")


# =====================================================
# STUDENT RECORDS
# =====================================================

elif page == "👨‍🎓 Student Records":

    show_header(
        "Student Records",
        "View the currently loaded student dataset"
    )

    df = st.session_state.student_data.copy()

    search = st.text_input(
        "🔍 Search by Student ID or Programme"
    )

    if search:

        mask = (
            df["Student_ID"].str.contains(
                search,
                case=False,
                na=False,
                regex=False
            )
            |
            df["Programme"].str.contains(
                search,
                case=False,
                na=False,
                regex=False
            )
        )

        df = df[mask]

    # Do not display raw APAAR IDs
    df["APAAR_ID"] = df["APAAR_ID"].apply(
        safe_display_id
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Student records currently reside in session memory. "
        "This prototype does not persist student records "
        "to the database."
    )


# =====================================================
# ANALYTICS
# =====================================================

elif page == "📊 Analytics":

    show_header(
        "Analytics Centre",
        "Understand enrolment patterns and data quality"
    )

    df = st.session_state.student_data.copy()

    st.subheader("📈 Programme-wise Enrolment")

    programme_counts = (
        df["Programme"]
        .value_counts()
        .rename_axis("Programme")
        .reset_index(name="Students")
    )

    if not programme_counts.empty:

        st.bar_chart(
            programme_counts.set_index("Programme")
        )

    st.markdown("---")

    st.subheader("🎯 Category-wise Distribution")

    category_counts = (
        df["Category"]
        .value_counts()
        .rename_axis("Category")
        .reset_index(name="Students")
    )

    st.bar_chart(
        category_counts.set_index("Category")
    )

    st.markdown("---")

    st.subheader("🪪 APAAR Data Quality")

    quality = pd.DataFrame({
        "Status": [
            "Format Passing",
            "Invalid Format",
            "Missing"
        ],
        "Count": [
            int(
                df["APAAR_ID"].apply(
                    valid_apaar_format
                ).sum()
            ),
            int(
                (
                    df["APAAR_ID"].apply(
                        lambda x: (
                            clean_text(x) != "" and
                            not valid_apaar_format(x)
                        )
                    )
                ).sum()
            ),
            int(
                df["APAAR_ID"].apply(
                    lambda x: clean_text(x) == ""
                ).sum()
            )
        ]
    })

    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "APAAR format checks are illustrative and do not "
        "establish authenticity."
    )


# =====================================================
# AUDIT HISTORY
# =====================================================

elif page == "🕒 Audit History":

    show_header(
        "Audit History",
        "Review recorded prototype actions"
    )

    with sqlite3.connect(DB_PATH) as conn:

        audit_df = pd.read_sql_query(
            """
            SELECT timestamp, action, details
            FROM audit_logs
            ORDER BY id DESC
            LIMIT 500
            """,
            conn
        )

    if audit_df.empty:

        st.info("No audit events recorded yet.")

    else:

        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "Prototype audit logs are not tamper-proof "
        "and do not identify authenticated users."
    )


# =====================================================
# SETTINGS
# =====================================================

elif page == "⚙️ Settings":

    show_header(
        "Platform Settings",
        "Configure demo institution details"
    )

    st.subheader("🏫 Institution Configuration")

    with st.form("settings_form"):

        institution_name = st.text_input(
            "Institution Name",
            value=st.session_state.institution_name
        )

        institution_id = st.text_input(
            "Demo Institution ID",
            value=st.session_state.institution_id
        )

        approved_intake = st.number_input(
            "Configured Approved Intake",
            min_value=0,
            max_value=100000,
            value=int(st.session_state.approved_intake)
        )

        submitted = st.form_submit_button(
            "💾 Save Settings"
        )

        if submitted:

            st.session_state.institution_name = institution_name

            st.session_state.institution_id = institution_id

            st.session_state.approved_intake = approved_intake

            log_action(
                "SETTINGS_UPDATED",
                json.dumps({
                    "institution": institution_name,
                    "institution_id": institution_id,
                    "approved_intake": approved_intake
                })
            )

            st.success("Settings updated successfully.")

    st.markdown("---")

    st.subheader("🔐 Security Notes")

    st.write("""
    - This prototype does not provide real authentication.
    - No official APAAR API is connected.
    - Do not use actual student personal information.
    - No official student verification is performed.
    - SQLite audit logs are demonstration-only.
    - Production deployment requires security testing,
      encryption, access control, consent management,
      retention policies and authorized integrations.
    """)


# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown("""
<center>
🎓 <b>APAAR Connect AI</b><br>
Student Data Management & Verification Prototype<br>
<small>Demonstration only | Not an official AICTE platform</small>
</center>
""", unsafe_allow_html=True)