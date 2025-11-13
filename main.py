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
                # (page in frames with max last_used index)
                mru_page = None
                mru_index = -1
                for p in frames:
                    # if page never used before, set to -1 (very old)
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

            st.subheader("Result (Manual Input)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total References", len(pages))
            with col2:
                st.metric("Page Faults", faults)
            with col3:
                st.metric("Page Fault Rate (%)", f"{fault_rate:.2f}")

            st.write("### Step-by-step MRU Table")
            st.dataframe(detail_df, use_container_width=True)

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
- Non-numeric cells or empty cells will be ignored  
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
            # Drop NaN and convert to int if possible
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

            st.markdown(f"## Case: `{col}`")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total References", len(pages))
            with col2:
                st.metric("Page Faults", faults)
            with col3:
                st.metric("Page Fault Rate (%)", f"{fault_rate:.2f}")

            st.write("### Step-by-step MRU Table")
            st.dataframe(detail_df, use_container_width=True)
            st.divider()

        if not numeric_cases_found:
            st.error("No numeric columns found. Please make sure your file has numeric page references.")
