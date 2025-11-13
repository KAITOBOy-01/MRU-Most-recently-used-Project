import streamlit as st
import pandas as pd
import re

# ---------------- MRU ALGORITHM ---------------- #

def mru_page_replacement(page_sequence, frame_count):
    """
    MRU (Most Recently Used) page replacement.
    page_sequence: list of ints (page references)
    frame_count: number of frames in memory
    Returns: faults, fault_rate, detail_df (for table)
    """
    frames = []              # current pages in memory
    last_used = {}           # page -> last used index
    faults = 0
    steps_data = []

    for i, page in enumerate(page_sequence):
        step = i + 1
        hit = page in frames

        if not hit:
            faults += 1
            # If there is still empty frame
            if len(frames) < frame_count:
                frames.append(page)
            else:
                # Find Most Recently Used page among frames
                mru_page = None
                mru_index = -1
                for p in frames:
                    idx = last_used.get(p, -1)
                    if idx > mru_index:
                        mru_index = idx
                        mru_page = p
                # Replace MRU page with new one
                replace_index = frames.index(mru_page)
                frames[replace_index] = page

        # Update last used index for this page
        last_used[page] = i

        # Snapshot frames for table (pad with '-' if not full yet)
        frame_state = frames.copy()
        while len(frame_state) < frame_count:
            frame_state.append('-')

        steps_data.append({
            "Step": step,
            "Page": page,
            "Frame State": " | ".join(str(x) for x in frame_state),
            "Hit/Fault": "Hit" if hit else "Fault"
        })

    total = len(page_sequence)
    fault_rate = (faults / total * 100) if total > 0 else 0.0
    detail_df = pd.DataFrame(steps_data)

    return faults, fault_rate, detail_df


# -------------- HELPER FUNCTIONS FOR UI -------------- #

def split_frame_state(state_str):
    # "11 | 12 | - | -" -> ["11", "12", "-", "-"]
    return [s.strip() for s in state_str.split("|")]

def render_results(title, pages, faults, fault_rate, detail_df, frame_count):
    """Render the modern cards + table for one case."""
    st.markdown(f"## 📁 {title}")

    # ----- Summary cards -----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div style="padding:20px;border-radius:15px;background:#1e1e1e;text-align:center;">
                <h3 style="margin-bottom:5px;">Total References</h3>
                <h1 style="color:#4FC3F7;margin-top:0px;">{len(pages)}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="padding:20px;border-radius:15px;background:#1e1e1e;text-align:center;">
                <h3 style="margin-bottom:5px;">Page Faults</h3>
                <h1 style="color:#FF8A80;margin-top:0px;">{faults}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div style="padding:20px;border-radius:15px;background:#1e1e1e;text-align:center;">
                <h3 style="margin-bottom:5px;">Fault Rate (%)</h3>
                <h1 style="color:#81C784;margin-top:0px;">{fault_rate:.2f}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 🧠 Step-by-Step MRU Execution")

    # Convert "Frame State" column into separate frame columns
    detail_df["Frame State"] = detail_df["Frame State"].apply(split_frame_state)

    expanded_df = detail_df.copy()

    max_frames = frame_count
    for i in range(max_frames):
        expanded_df[f"Frame {i+1}"] = expanded_df["Frame State"].apply(
            lambda x, idx=i: x[idx] if idx < len(x) else "-"
        )

    expanded_df.drop(columns=["Frame State"], inplace=True)

    # Color badges for Hit / Fault
    def hit_badge(val):
        if val == "Hit":
            return '<span style="color:#00e676;font-weight:bold;">🟢 HIT</span>'
        else:
            return '<span style="color:#ff5252;font-weight:bold;">🔴 FAULT</span>'

    expanded_df["Status"] = expanded_df["Hit/Fault"].apply(hit_badge)
    expanded_df.drop(columns=["Hit/Fault"], inplace=True)

    # Neater column order
    cols_order = ["Step", "Page"] + [f"Frame {i+1}" for i in range(max_frames)] + ["Status"]
    expanded_df = expanded_df[cols_order]

    # Simple CSS for table
    st.markdown(
        """
        <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            padding: 6px 10px;
            text-align: center;
        }
        thead tr {
            background-color: #212121;
        }
        tbody tr:nth-child(odd) {
            background-color: #121212;
        }
        tbody tr:nth-child(even) {
            background-color: #1a1a1a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.write(expanded_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.divider()


# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(
    page_title="MRU Page Replacement Simulator",
    layout="wide"
)

st.title("🧠 MRU (Most Recently Used) Page Replacement")
st.write("""
This app simulates **MRU page replacement** and calculates the **page fault rate**.

- Input page references manually **or** upload **CSV / Excel** file  
- Max **20 page references** per case  
- Choose number of frames between **3 and 8**
""")

# Select number of frames
frame_count = st.slider(
    "Select number of frames",
    min_value=3,
    max_value=8,
    value=3
)

st.divider()

# Input method
input_method = st.radio(
    "Choose input method",
    ["Manual input", "Upload CSV / Excel"],
    horizontal=True
)

# ------------- MANUAL INPUT ------------- #
if input_method == "Manual input":
    example = "7 0 1 2 0 3 0 4 2 3 0 3 2"
    seq_str = st.text_input(
        "Enter page reference string (separated by space or comma)",
        value=example
    )

    if st.button("Run MRU (Manual Input)"):
        if not seq_str.strip():
            st.error("Please enter at least one page number.")
        else:
            # Parse numbers from string
            try:
                tokens = re.split(r"[,\s]+", seq_str.strip())
                pages = [int(t) for t in tokens if t != ""]
            except ValueError:
                st.error("Please enter only integer page numbers.")
                st.stop()

            if len(pages) == 0:
                st.error("No valid page numbers found.")
                st.stop()

            if len(pages) > 20:
                st.error(f"Maximum is 20 pages, but you gave {len(pages)}.")
                st.stop()

            faults, fault_rate, detail_df = mru_page_replacement(pages, frame_count)

            render_results("Manual Input", pages, faults, fault_rate, detail_df, frame_count)

# ------------- FILE INPUT ------------- #
else:
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file (max 20 rows per case)",
        type=["csv", "xlsx", "xls"]
    )

    st.info("""
**File format suggestions:**
- Each **column** = one case (sequence of pages)  
- Each **row** = next page reference  
- Non-numeric or empty cells are ignored  
- Max **20 rows** (page references) per column
""")

    if uploaded_file is not None and st.button("Run MRU (File Input)"):
        # Read file
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        if df.empty:
            st.error("File is empty.")
            st.stop()

        if len(df) > 20:
            st.error(f"Maximum is 20 rows (page references), but file has {len(df)} rows.")
            st.stop()

        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)

        # Use each column as one case
        numeric_cases_found = False

        for col in df.columns:
            series = df[col].dropna()

            if series.empty:
                continue

            # Try to convert to int
            try:
                pages = [int(x) for x in series]
            except ValueError:
                # Skip non-numeric column
                continue

            numeric_cases_found = True

            faults, fault_rate, detail_df = mru_page_replacement(pages, frame_count)

            render_results(f"Case: {col}", pages, faults, fault_rate, detail_df, frame_count)

        if not numeric_cases_found:
            st.error("No numeric columns found. Please make sure your file has numeric page references.")
