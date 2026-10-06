import io
import tempfile
import pandas as pd
import pyreadstat
import streamlit as st

# Configure Streamlit Page Layout
st.set_page_config(
    page_title="Live Quota & Status Dashboard", page_icon="📊", layout="wide"
)

# Custom Styling for Dark Theme Look
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 8px; border: 1px solid #30333d; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📊 Live Status Calculation & Quota Tracker")
st.markdown("---")

# ==========================================
# SECTION 1: LIVE QUOTA TARGET ADJUSTMENTS
# ==========================================
st.markdown("### 🎯 Live Quota Target Adjustments")
col1, col2, col3 = st.columns(3)

with col1:
    business_target = st.number_input(
        "Business (Growth) Target", min_value=0, value=4700, step=50
    )
with col2:
    enterprise_target = st.number_input(
        "Enterprise (R10Mil) Target", min_value=0, value=1400, step=50
    )
with col3:
    pubsc_target = st.number_input(
        "PUBSC Target", min_value=0, value=500, step=50
    )

total_target_quota = business_target + enterprise_target + pubsc_target

st.markdown("---")

# ==========================================
# SECTION 2: SEGMENT-LEVEL QUOTA BREAKDOWN
# ==========================================
st.markdown("### 🔢 Segment-Level Quota Breakdown Inputs")
st.markdown(
    "Specify exact individual segment quotas below for detailed tracking:"
)

seg_cols = st.columns(4)
with seg_cols[0]:
    q_rom_r1m = st.number_input("R0M-R1M Quota", min_value=0, value=1600, step=25)
with seg_cols[1]:
    q_r1m_r5m = st.number_input("R1M-R5M Quota", min_value=0, value=1100, step=25)
with seg_cols[2]:
    q_r5m_r10m = st.number_input(
        "R5M-R10M Quota", min_value=0, value=900, step=25
    )
with seg_cols[3]:
    q_r10_r60m = st.number_input(
        "R10-R60M Quota", min_value=0, value=1100, step=25
    )

seg_cols_2 = st.columns(2)
with seg_cols_2[0]:
    q_r60_r150m = st.number_input(
        "R60-R150M Quota", min_value=0, value=900, step=25
    )
with seg_cols_2[1]:
    q_r150m_plus = st.number_input(
        "R150M+ Quota", min_value=0, value=500, step=25
    )

total_segment_quota = (
    q_rom_r1m
    + q_r1m_r5m
    + q_r5m_r10m
    + q_r10_r60m
    + q_r60_r150m
    + q_r150m_plus
)

st.markdown("---")

# ==========================================
# SECTION 3: UPLOAD SPSS DATASETS (.sav)
# ==========================================
st.markdown("### 📁 Upload Latest SPSS Datasets for Live Status Calculation")
up_col1, up_col2, up_col3 = st.columns(3)

with up_col1:
    file_grow = st.file_uploader("Upload Growth (.sav)", type=["sav"])
with up_col2:
    file_rmw = st.file_uploader("Upload R10Mil (.sav)", type=["sav"])
with up_col3:
    file_pubw = st.file_uploader("Upload PUBSC (.sav)", type=["sav"])


# Helper function to process uploaded .sav file securely via temporary path
def load_spss_data(uploaded_file):
    if uploaded_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sav") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            df, meta = pyreadstat.read_sav(tmp_path, apply_value_formats=True)
            df.columns = [str(c).upper() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None
    return None


df_grow = load_spss_data(file_grow)
df_rmw = load_spss_data(file_rmw)
df_pubw = load_spss_data(file_pubw)


# Calculation Logic for Completions (V9999 == 'Continue')
def count_completions(df):
    if df is not None and "V9999" in df.columns:
        str_val = df["V9999"].astype(str).str.lower()
        completed_filter = str_val.str.contains("continue", na=False)
        return int(completed_filter.sum())
    return 0


achieved_growth = count_completions(df_grow)
achieved_rmw = count_completions(df_rmw)
achieved_pubw = count_completions(df_pubw)

total_achieved = achieved_growth + achieved_rmw + achieved_pubw
total_outstanding = max(0, total_target_quota - total_achieved)
overall_progress = (
    (total_achieved / total_target_quota * 100)
    if total_target_quota > 0
    else 0.0
)

st.markdown("---")

# ==========================================
# SECTION 4: EXECUTIVE SUMMARY OVERVIEW
# ==========================================
st.markdown("### 📋 Executive Summary Overview")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(label="Total Target Quota", value=f"{total_target_quota:,.0f}")
with m2:
    st.metric(
        label="Total Achieved",
        value=f"{total_achieved:,.0f}",
        delta=f"{overall_progress:.1f}% Complete",
    )
with m3:
    st.metric(label="Total Outstanding", value=f"{total_outstanding:,.0f}")
with m4:
    st.metric(label="Overall Progress", value=f"{overall_progress:.1f}%")

# High-Level Summary Table
summary_data = {
    "Segment": ["Business", "Enterprise", "PUBSC", "Total"],
    "TOTAL Target": [
        business_target,
        enterprise_target,
        pubsc_target,
        total_target_quota,
    ],
    "TOTAL Achieved": [
        achieved_growth,
        achieved_rmw,
        achieved_pubw,
        total_achieved,
    ],
    "TOTAL Outstanding": [
        max(0, business_target - achieved_growth),
        max(0, enterprise_target - achieved_rmw),
        max(0, pubsc_target - achieved_pubw),
        total_outstanding,
    ],
}
df_summary = pd.DataFrame(summary_data)
st.dataframe(df_summary, use_container_width=True, hide_index=True)

st.markdown("---")

# ==========================================
# SECTION 5: SEGMENT QUOTAS EXECUTIVE SUMMARY BREAKDOWN
# ==========================================
st.markdown("### 📊 Segment Quotas Executive Summary Breakdown")


def get_segment_achieved(target_df, segment_keywords):
    count = 0
    if target_df is not None and "V9999" in target_df.columns and "V44011" in target_df.columns:
        str_val = target_df["V9999"].astype(str).str.lower()
        completed = str_val.str.contains("continue", na=False)

        matched_seg = pd.Series(False, index=target_df.index)
        for kw in segment_keywords:
            matched_seg = matched_seg | (
                target_df["V44011"]
                .astype(str)
                .str.contains(kw, case=False, na=False)
            )
        count = int((completed & matched_seg).sum())
    return count


ach_rom_r1m = get_segment_achieved(df_grow, ["r0m-r1m"])
ach_r1m_r5m = get_segment_achieved(df_grow, ["r1m-r5m"])
ach_r5m_r10m = get_segment_achieved(df_grow, ["r5m-r10"])

ach_r10_r60m = get_segment_achieved(df_rmw, ["r10m-r60m"])
ach_r60_r150m = get_segment_achieved(df_rmw, ["r60m-r150"])
ach_r150m_plus = get_segment_achieved(df_rmw, ["r150m+"])

total_seg_achieved = (
    ach_rom_r1m
    + ach_r1m_r5m
    + ach_r5m_r10m
    + ach_r10_r60m
    + ach_r60_r150m
    + ach_r150m_plus
)
total_seg_outstanding = max(0, total_segment_quota - total_seg_achieved)

seg_breakdown_data = {
    "Segment": [
        "R0M-R1M",
        "R1M-R5M",
        "R5M-R10M",
        "R10-R60M",
        "R60-R150M",
        "R150M+",
        "Total",
    ],
    "TOTAL Target": [
        q_rom_r1m,
        q_r1m_r5m,
        q_r5m_r10m,
        q_r10_r60m,
        q_r60_r150m,
        q_r150m_plus,
        total_segment_quota,
    ],
    "TOTAL Achieved": [
        ach_rom_r1m,
        ach_r1m_r5m,
        ach_r5m_r10m,
        ach_r10_r60m,
        ach_r60_r150m,
        ach_r150m_plus,
        total_seg_achieved,
    ],
    "TOTAL Outstanding": [
        max(0, q_rom_r1m - ach_rom_r1m),
        max(0, q_r1m_r5m - ach_r1m_r5m),
        max(0, q_r5m_r10m - ach_r5m_r10m),
        max(0, q_r10_r60m - ach_r10_r60m),
        max(0, q_r60_r150m - ach_r60_r150m),
        max(0, q_r150m_plus - ach_r150m_plus),
        total_seg_outstanding,
    ],
}

df_seg_breakdown = pd.DataFrame(seg_breakdown_data)
st.dataframe(df_seg_breakdown, use_container_width=True, hide_index=True)

st.markdown("---")

# ==========================================
# SECTION 6: BUSINESS REGIONAL & SEGMENT BREAKDOWN (GROWTH DATASET)
# ==========================================
standard_subregions = [
    "Eastern Cape",
    "Free State",
    "Gauteng East",
    "Gauteng South Central/Klipriver",
    "Gauteng Tshwane East",
    "Gauteng Tshwane North",
    "Gauteng Tshwane South",
    "Gauteng West-Rand",
    "Greater Sandton",
    "Gauteng Midrand",
    "KZN North",
    "KZN South",
    "KZN West",
    "Limpopo",
    "Mpumalanga",
    "North West",
    "Northern Cape",
    "Western Cape",
]

standard_regions = ["Cape", "Gauteng North", "Gauteng South Central", "Inland", "KwaZulu-Natal"]

def map_subregion_and_region(row_sub, row_reg):
    sub_str = str(row_sub).strip() if pd.notnull(row_sub) else ""
    reg_str = str(row_reg).strip() if pd.notnull(row_reg) else ""
    sub_lower = sub_str.lower()
    
    if "eastern cape" in sub_lower:
        return "Eastern Cape", "Cape"
    elif "free state" in sub_lower:
        return "Free State", "Inland"
    elif "gauteng east" in sub_lower:
        return "Gauteng East", "Gauteng South Central"
    elif "klipriver" in sub_lower or "south central" in sub_lower:
        return "Gauteng South Central/Klipriver", "Gauteng South Central"
    elif "tshwane east" in sub_lower:
        return "Gauteng Tshwane East", "Gauteng North"
    elif "tshwane north" in sub_lower:
        return "Gauteng Tshwane North", "Gauteng North"
    elif "tshwane south" in sub_lower:
        return "Gauteng Tshwane South", "Gauteng North"
    elif "west-rand" in sub_lower or "west rand" in sub_lower:
        return "Gauteng West-Rand", "Gauteng South Central"
    elif "greater sandton" in sub_lower or "sandton" in sub_lower:
        if "gn growth" in sub_lower or "north" in reg_str.lower():
            return "Greater Sandton", "Gauteng North"
        return "Greater Sandton", "Gauteng South Central"
    elif "midrand" in sub_lower:
        if "gn growth" in sub_lower or "north" in reg_str.lower():
            return "Gauteng Midrand", "Gauteng North"
        return "Gauteng Midrand", "Gauteng South Central"
    elif "kzn north" in sub_lower:
        return "KZN North", "KwaZulu-Natal"
    elif "kzn south" in sub_lower:
        return "KZN South", "KwaZulu-Natal"
    elif "kzn west" in sub_lower or "kzn" in sub_lower:
        return "KZN West", "KwaZulu-Natal"
    elif "limpopo" in sub_lower:
        return "Limpopo", "Inland"
    elif "mpumalanga" in sub_lower or "moumalanga" in sub_lower:
        return "Mpumalanga", "Inland"
    elif "north west" in sub_lower:
        return "North West", "Inland"
    elif "northern cape" in sub_lower:
        return "Northern Cape", "Inland"
    elif "western cape" in sub_lower:
        return "Western Cape", "Cape"
    
    return sub_str if sub_str else "Unknown", reg_str if reg_str else "Unknown"

bus_reg_matrix = pd.DataFrame(0, index=standard_subregions, columns=standard_regions + ["Total"])

if df_grow is not None and "V9999" in df_grow.columns and "V13290" in df_grow.columns:
    str_val = df_grow["V9999"].astype(str).str.lower()
    completed_df = df_grow[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_df.iterrows():
        raw_sub = row.get("V13290", "")
        raw_reg = row.get("V12290", "")
        mapped_sub, mapped_reg = map_subregion_and_region(raw_sub, raw_reg)
        if mapped_sub in bus_reg_matrix.index and mapped_reg in bus_reg_matrix.columns:
            bus_reg_matrix.loc[mapped_sub, mapped_reg] += 1

bus_reg_matrix["Total"] = bus_reg_matrix[standard_regions].sum(axis=1)

standard_segments = ["R0M-R1M", "R1M-R5M", "R5M-R10M", "R10-R60M"]
bus_seg_matrix = pd.DataFrame(0, index=standard_segments, columns=standard_regions + ["Total", "Quota", "Outstanding"])
bus_quotas = {"R0M-R1M": 1600, "R1M-R5M": 1100, "R5M-R10M": 900, "R10-R60M": 1100}

if df_grow is not None and "V9999" in df_grow.columns and "V13290" in df_grow.columns and "V44011" in df_grow.columns:
    str_val = df_grow["V9999"].astype(str).str.lower()
    completed_df = df_grow[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_df.iterrows():
        raw_sub = row.get("V13290", "")
        raw_reg = row.get("V12290", "")
        _, mapped_reg = map_subregion_and_region(raw_sub, raw_reg)
        
        v44 = str(row.get("V44011", "")).lower()
        seg_name = None
        if "r0m-r1m" in v44:
            seg_name = "R0M-R1M"
        elif "r1m-r5m" in v44:
            seg_name = "R1M-R5M"
        elif "r5m-r10" in v44:
            seg_name = "R5M-R10M"
        elif "r10m-r60m" in v44:
            seg_name = "R10-R60M"
            
        if seg_name and seg_name in bus_seg_matrix.index and mapped_reg in bus_seg_matrix.columns:
            bus_seg_matrix.loc[seg_name, mapped_reg] += 1

bus_seg_matrix["Total"] = bus_seg_matrix[standard_regions].sum(axis=1)
for seg in standard_segments:
    q_val = bus_quotas.get(seg, 0)
    ach_val = bus_seg_matrix.loc[seg, "Total"]
    bus_seg_matrix.loc[seg, "Quota"] = q_val
    bus_seg_matrix.loc[seg, "Outstanding"] = max(0, q_val - ach_val)

crosstab_segments = ["R0m-R1m", "R1m-R5m", "R5m-R10"]
bus_reg_seg_crosstab = pd.DataFrame(0, index=standard_subregions, columns=crosstab_segments + ["TOTAL"])

if df_grow is not None and "V9999" in df_grow.columns and "V13290" in df_grow.columns and "V44011" in df_grow.columns:
    str_val = df_grow["V9999"].astype(str).str.lower()
    completed_df = df_grow[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_df.iterrows():
        raw_sub = row.get("V13290", "")
        raw_reg = row.get("V12290", "")
        mapped_sub, _ = map_subregion_and_region(raw_sub, raw_reg)
        
        v44 = str(row.get("V44011", "")).lower()
        col_name = None
        if "r0m-r1m" in v44:
            col_name = "R0m-R1m"
        elif "r1m-r5m" in v44:
            col_name = "R1m-R5m"
        elif "r5m-r10" in v44:
            col_name = "R5m-R10"
            
        if mapped_sub in bus_reg_seg_crosstab.index and col_name in bus_reg_seg_crosstab.columns:
            bus_reg_seg_crosstab.loc[mapped_sub, col_name] += 1

bus_reg_seg_crosstab["TOTAL"] = bus_reg_seg_crosstab[crosstab_segments].sum(axis=1)
total_row = bus_reg_seg_crosstab.sum(numeric_only=True)
bus_reg_seg_crosstab.loc["TOTAL"] = total_row


# ==========================================
# SECTION 7: ENTERPRISE (R10MIL) REGIONAL & SEGMENT BREAKDOWN
# ==========================================
ent_subregions = [
    "Eastern Cape",
    "Free State",
    "Gauteng East",
    "Gauteng Klipriver",
    "Gauteng North",
    "Gauteng South-West",
    "Gauteng Tshwane",
    "Greater Sandton",
    "KZN Coastal",
    "KZN Inland",
    "Limpopo",
    "Midrand",
    "Mpumalanga",
    "North West",
    "Northern Cape",
    "Western Cape Inland",
    "Western Cape Metro",
]

ent_regions = ["Cape", "Gauteng South and Central", "Gauteng-North", "Inland", "KwaZulu-Natal"]

def map_ent_subregion_and_region(row_sub, row_reg):
    sub_str = str(row_sub).strip() if pd.notnull(row_sub) else ""
    reg_str = str(row_reg).strip() if pd.notnull(row_reg) else ""
    sub_upper = sub_str.upper()
    
    if "EASTERN CAPE" in sub_upper:
        return "Eastern Cape", "Cape"
    elif "FREE STATE" in sub_upper:
        return "Free State", "Inland"
    elif "GAUTENG EAST" in sub_upper:
        return "Gauteng East", "Gauteng-North"
    elif "GAUTENG KLIPRIVER" in sub_upper:
        return "Gauteng Klipriver", "Gauteng-North"
    elif "GAUTENG NORTH" in sub_upper:
        return "Gauteng North", "Gauteng-North"
    elif "GAUTENG WEST" in sub_upper or "SOUTH-WEST" in sub_upper:
        return "Gauteng South-West", "Gauteng-North"
    elif "GAUTENG TSHWANE" in sub_upper:
        return "Gauteng Tshwane", "Gauteng South and Central"
    elif "GREATER SANDTON" in sub_upper:
        return "Greater Sandton", "Gauteng South and Central"
    elif "KZN COASTAL" in sub_upper:
        return "KZN Coastal", "KwaZulu-Natal"
    elif "KZN INLAND" in sub_upper:
        return "KZN Inland", "KwaZulu-Natal"
    elif "LIMPOPO" in sub_upper:
        return "Limpopo", "Inland"
    elif "MIDRAND" in sub_upper:
        return "Midrand", "Gauteng South and Central"
    elif "MPUMALANGA" in sub_upper:
        return "Mpumalanga", "Inland"
    elif "NORTH WEST" in sub_upper:
        return "North West", "Inland"
    elif "NORTHERN CAPE" in sub_upper:
        return "Northern Cape", "Inland"
    elif "WESTERN CAPE INLAND" in sub_upper:
        return "Western Cape Inland", "Cape"
    elif "WESTERN CAPE METRO" in sub_upper:
        return "Western Cape Metro", "Cape"
        
    return sub_str if sub_str else "Unknown", reg_str if reg_str else "Unknown"

ent_reg_matrix = pd.DataFrame(0, index=ent_subregions, columns=ent_regions + ["Total"])

if df_rmw is not None and "V9999" in df_rmw.columns and "V13290" in df_rmw.columns:
    str_val = df_rmw["V9999"].astype(str).str.lower()
    completed_ent = df_rmw[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_ent.iterrows():
        raw_sub = row.get("V13290", "")
        raw_reg = row.get("V12290", "")
        mapped_sub, mapped_reg = map_ent_subregion_and_region(raw_sub, raw_reg)
        if mapped_sub in ent_reg_matrix.index and mapped_reg in ent_reg_matrix.columns:
            ent_reg_matrix.loc[mapped_sub, mapped_reg] += 1

ent_reg_matrix["Total"] = ent_reg_matrix[ent_regions].sum(axis=1)

ent_segments = ["R10-R60M", "R60-R150M", "R150M+"]
ent_seg_matrix = pd.DataFrame(0, index=ent_segments, columns=ent_regions + ["Total", "Quota", "Outstanding"])
ent_quotas = {"R10-R60M": 550, "R60-R150M": 450, "R150M+": 250}

if df_rmw is not None and "V9999" in df_rmw.columns and "V13290" in df_rmw.columns and "V44011" in df_rmw.columns:
    str_val = df_rmw["V9999"].astype(str).str.lower()
    completed_ent = df_rmw[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_ent.iterrows():
        raw_sub = row.get("V13290", "")
        raw_reg = row.get("V12290", "")
        _, mapped_reg = map_ent_subregion_and_region(raw_sub, raw_reg)
        
        v44 = str(row.get("V44011", "")).lower()
        seg_name = None
        if "r10m-r60m" in v44 or "r10-r60m" in v44:
            seg_name = "R10-R60M"
        elif "r60m-r150" in v44 or "r60-r150m" in v44:
            seg_name = "R60-R150M"
        elif "r150m+" in v44:
            seg_name = "R150M+"
            
        if seg_name and seg_name in ent_seg_matrix.index and mapped_reg in ent_seg_matrix.columns:
            ent_seg_matrix.loc[seg_name, mapped_reg] += 1

ent_seg_matrix["Total"] = ent_seg_matrix[ent_regions].sum(axis=1)
for seg in ent_segments:
    q_val = ent_quotas.get(seg, 0)
    ach_val = ent_seg_matrix.loc[seg, "Total"]
    ent_seg_matrix.loc[seg, "Quota"] = q_val
    ent_seg_matrix.loc[seg, "Outstanding"] = max(0, q_val - ach_val)

crosstab_ent_segments = ["R10m-R60m", "R150m+", "R60m-R150"]
ent_reg_seg_crosstab = pd.DataFrame(0, index=ent_subregions, columns=crosstab_ent_segments + ["TOTAL"])

if df_rmw is not None and "V9999" in df_rmw.columns and "V13290" in df_rmw.columns and "V44011" in df_rmw.columns:
    str_val = df_rmw["V9999"].astype(str).str.lower()
    completed_ent = df_rmw[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_ent.iterrows():
        raw_sub = row.get("V13290", "")
        raw_reg = row.get("V12290", "")
        mapped_sub, _ = map_ent_subregion_and_region(raw_sub, raw_reg)
        
        v44 = str(row.get("V44011", "")).lower()
        col_name = None
        if "r10m-r60m" in v44 or "r10-r60m" in v44:
            col_name = "R10m-R60m"
        elif "r150m+" in v44:
            col_name = "R150m+"
        elif "r60m-r150" in v44 or "r60-r150m" in v44:
            col_name = "R60m-R150"
            
        if mapped_sub in ent_reg_seg_crosstab.index and col_name in ent_reg_seg_crosstab.columns:
            ent_reg_seg_crosstab.loc[mapped_sub, col_name] += 1

ent_reg_seg_crosstab["TOTAL"] = ent_reg_seg_crosstab[crosstab_ent_segments].sum(axis=1)
ent_total_row = ent_reg_seg_crosstab.sum(numeric_only=True)
ent_reg_seg_crosstab.loc["TOTAL"] = ent_total_row


# ==========================================
# SECTION 8: PUBSC (PUBLIC SECTOR) REGIONAL & SECTOR CROSSTAB (V12290 & V13290)
# ==========================================
pubsc_regions = [
    "EASTERN CAPE",
    "FREE STATE",
    "GAUTENG",
    "KWAZULU-NATAL",
    "LIMPOPO",
    "MPUMALANGA",
    "NORTH WEST",
    "NORTHERN CAPE",
    "WESTERN CAPE"
]

pubsc_sectors = [
    "NON-PROFIT ORGANISATION",
    "PUBLIC SECTOR COLLEGES & FET'S",
    "PUBLIC SECTOR EMBASSIES",
    "PUBLIC SECTOR LOCAL GOVERMENT",
    "PUBLIC SECTOR PROVINCIAL GOVER",
    "PUBLIC SECTOR PUBLIC SCHOOLS",
    "PUBLIC SECTOR UNIONS & POLITIC"
]

def map_pubsc_region_and_sector(row_reg, row_sec):
    reg_str = str(row_reg).strip().upper() if pd.notnull(row_reg) else ""
    sec_str = str(row_sec).strip().upper() if pd.notnull(row_sec) else ""
    
    mapped_reg = "UNKNOWN"
    if "EASTERN" in reg_str:
        mapped_reg = "EASTERN CAPE"
    elif "FREE" in reg_str:
        mapped_reg = "FREE STATE"
    elif "GAUTENG" in reg_str:
        mapped_reg = "GAUTENG"
    elif "KWAZULU" in reg_str or "KZN" in reg_str:
        mapped_reg = "KWAZULU-NATAL"
    elif "LIMPOPO" in reg_str:
        mapped_reg = "LIMPOPO"
    elif "MPUMALANGA" in reg_str:
        mapped_reg = "MPUMALANGA"
    elif "NORTH WEST" in reg_str:
        mapped_reg = "NORTH WEST"
    elif "NORTHERN" in reg_str:
        mapped_reg = "NORTHERN CAPE"
    elif "WESTERN" in reg_str:
        mapped_reg = "WESTERN CAPE"
        
    mapped_sec = "UNKNOWN"
    for s in pubsc_sectors:
        if s in sec_str or sec_str in s:
            mapped_sec = s
            break
            
    return mapped_reg, mapped_sec

pubsc_crosstab = pd.DataFrame(0, index=pubsc_sectors, columns=pubsc_regions + ["TOTAL"])

if df_pubw is not None and "V9999" in df_pubw.columns and "V12290" in df_pubw.columns and "V13290" in df_pubw.columns:
    str_val = df_pubw["V9999"].astype(str).str.lower()
    completed_pub = df_pubw[str_val.str.contains("continue", na=False)].copy()
    
    for idx, row in completed_pub.iterrows():
        raw_reg = row.get("V12290", "")
        raw_sec = row.get("V13290", "")
        mapped_reg, mapped_sec = map_pubsc_region_and_sector(raw_reg, raw_sec)
        
        if mapped_sec in pubsc_crosstab.index and mapped_reg in pubsc_crosstab.columns:
            pubsc_crosstab.loc[mapped_sec, mapped_reg] += 1

pubsc_crosstab["TOTAL"] = pubsc_crosstab[pubsc_regions].sum(axis=1)
pubsc_total_row = pubsc_crosstab.sum(numeric_only=True)
pubsc_crosstab.loc["TOTAL"] = pubsc_total_row


# ==========================================
# UI TABS FOR BREAKDOWNS (SEPARATED TABS)
# ==========================================
st.markdown("### 🔍 Live Regional & Segment Breakdown Tables")
tab_bus, tab_ent, tab_pub = st.tabs(["Business Breakdown", "Enterprise Breakdown", "PUBSC Breakdown"])

with tab_bus:
    st.markdown("#### Business Regional Breakdown")
    st.dataframe(bus_reg_matrix, use_container_width=True)
    
    st.markdown("#### Business Segment Breakdown Matrix (Quota & Outstanding)")
    st.dataframe(bus_seg_matrix, use_container_width=True)
    
    st.markdown("#### Business Regional vs. Segments Crosstab (Sub-regions as Rows, Segments as Columns)")
    st.dataframe(bus_reg_seg_crosstab, use_container_width=True)

with tab_ent:
    st.markdown("#### Enterprise Regional Breakdown")
    st.dataframe(ent_reg_matrix, use_container_width=True)
    
    st.markdown("#### Enterprise Segment Breakdown Matrix (Quota & Outstanding)")
    st.dataframe(ent_seg_matrix, use_container_width=True)
    
    st.markdown("#### Enterprise Regional vs. Segments Crosstab (Sub-regions as Rows, Segments as Columns)")
    st.dataframe(ent_reg_seg_crosstab, use_container_width=True)

with tab_pub:
    st.markdown("#### Public Sector (PUBSC) Regional vs. Sector Crosstab")
    st.dataframe(pubsc_crosstab, use_container_width=True)


# ==========================================
# SECTION 9: EXCEL DOWNLOAD WORKBOOK GENERATION
# ==========================================
st.markdown("---")
st.markdown("### 📥 Download PM Update Workbook")

def create_pm_workbook():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Summary on its own
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Update Business
        workbook = writer.book
        ws_bus = workbook.create_sheet(title='Update Business')
        bus_reg_matrix.to_excel(writer, sheet_name='Update Business', startrow=0, startcol=0)
        bus_seg_matrix.to_excel(writer, sheet_name='Update Business', startrow=0, startcol=10)
        bus_reg_seg_crosstab.to_excel(writer, sheet_name='Update Business', startrow=22, startcol=0)
        
        # Sheet 3: Update Enterprise
        ws_ent = workbook.create_sheet(title='Update Enterprise')
        ent_reg_matrix.to_excel(writer, sheet_name='Update Enterprise', startrow=0, startcol=0)
        ent_seg_matrix.to_excel(writer, sheet_name='Update Enterprise', startrow=0, startcol=10)
        ent_reg_seg_crosstab.to_excel(writer, sheet_name='Update Enterprise', startrow=22, startcol=0)
        
        # Sheet 4: Update PUBSC
        ws_pub = workbook.create_sheet(title='Update PUBSC')
        pubsc_crosstab.to_excel(writer, sheet_name='Update PUBSC', startrow=0, startcol=0)

    return output.getvalue()

excel_data = create_pm_workbook()
st.download_button(
    label="📊 Generate & Download Exact PM Update Workbook",
    data=excel_data,
    file_name="Star_Detailed_Update_Live.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
