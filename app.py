from pathlib import Path
import io, re
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps
from motor_reader.ocr import NameplateOCR, annotate
from motor_reader.parser import parse_nameplate, confidence_summary, FIELDS

st.set_page_config(page_title="Motor Nameplate Reader", page_icon="⚙️", layout="wide")
st.markdown("""
<style>
.stApp{background:#100d0b;color:#eee7dc}
section[data-testid="stSidebar"]{background:#19130f}
h1,h2,h3{color:#ff9a32!important}
div[data-testid="stMetric"]{background:#201710;padding:12px;border-radius:8px;border:1px solid #57351d}
</style>
""", unsafe_allow_html=True)
st.title("⚙️ MOTOR NAMEPLATE READER")
st.caption("Read motor nameplate photos · Extract structured specifications · Export Excel")

with st.sidebar:
    st.subheader("Processing settings")
    device = st.selectbox("Device", ["cpu", "gpu"], index=0, help="GPU requires a compatible PyTorch/CUDA setup.")
    style = st.selectbox("OCR Style", ["auto", "detailed"], index=0)
    st.divider()
    st.caption("OCR engine: EasyOCR · Language: English")

left, right = st.columns([1.08, 1])
with left:
    st.subheader("LOAD PHOTO / LOAD FOLDER")
    uploads = st.file_uploader("Select nameplate image(s)", type=["jpg","jpeg","png","bmp","webp"], accept_multiple_files=True)
    run = st.button("▶ Scan nameplates", type="primary", use_container_width=True, disabled=not uploads)
    st.caption("Tip: use a sharp, straight-on photo with readable plate text.")
with right:
    st.subheader("Scan status")
    st.info(f"{len(uploads) if uploads else 0} image(s) selected · Device: {device.upper()} · Style: {style.upper()}")

if "records" not in st.session_state: st.session_state.records = []
if "raw" not in st.session_state: st.session_state.raw = []

if run and uploads:
    try:
        with st.spinner("Loading OCR model… first run may take a few minutes"):
            reader = NameplateOCR(device=device)
        progress = st.progress(0, text="Scanning images…")
        records, raw_rows = [], []
        for i, upload in enumerate(uploads):
            pil = Image.open(upload)
            pil = ImageOps.exif_transpose(pil).convert("RGB")
            image = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            with st.spinner(f"Reading {upload.name} ({i+1}/{len(uploads)})"):
                lines, _ = reader.read(image)
            raw_text = "\n".join(x.text for x in lines)
            fields = parse_nameplate(raw_text)
            fields["File"] = upload.name
            fields["OCR Confidence"] = confidence_summary(lines)
            records.append(fields)
            raw_rows.append({"file":upload.name,"raw":raw_text,"image":image,"lines":lines})
            progress.progress((i+1)/len(uploads), text=f"Processed {i+1}/{len(uploads)}")
        st.session_state.records = records
        st.session_state.raw = raw_rows
        st.success(f"Done · {len(records)} plate(s) processed. Review and edit the table below.")
    except Exception as e:
        st.error(f"OCR initialization or processing failed: {e}")
        st.info("Install dependencies with `pip install -r requirements.txt`. For GPU, install a PyTorch build matching your CUDA version.")

if st.session_state.raw:
    st.divider()
    st.subheader("OCR Results")
    tabs = st.tabs([x["file"] for x in st.session_state.raw])
    for tab, item in zip(tabs, st.session_state.raw):
        with tab:
            a,b = st.columns([1.15,1])
            with a:
                marked = annotate(item["image"], item["lines"])
                st.image(cv2.cvtColor(marked,cv2.COLOR_BGR2RGB), caption="Detected text regions", use_container_width=True)
            with b:
                st.markdown("**RAW OCR**")
                st.text_area("Recognized text", item["raw"], height=220, key="raw_"+item["file"])
                st.metric("Average OCR confidence", f"{confidence_summary(item['lines'])}%")
    st.divider()
    st.subheader("FORMATTED MOTOR INFORMATION")
    df = pd.DataFrame(st.session_state.records)
    preferred = ["File"] + FIELDS + ["OCR Confidence"]
    df = df[[c for c in preferred if c in df.columns]]
    edited = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="motor_editor")
    st.session_state.records = edited.to_dict(orient="records")
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        edited.to_excel(writer, index=False, sheet_name="Motor Nameplates")
        for item in st.session_state.raw:
            pd.DataFrame([{"File":item["file"],"Raw OCR":item["raw"]}]).to_excel(
                writer, index=False, sheet_name=re.sub(r"[^A-Za-z0-9]","",Path(item["file"]).stem)[:25] or "OCR"
            )
    st.download_button("⬇ Export Excel", data=out.getvalue(),
                       file_name="motor_nameplate_results.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary")
else:
    st.markdown("---")
    st.markdown("**Extracted fields**")
    st.write("Manufacturer · Model · Serial · Phase · Voltage · Current · Power · Speed · Frequency · Power Factor · Efficiency · IP Rating · Insulation · Mounting · Duty · Frame · Standard")
    st.caption("Upload one or more images, then click Scan nameplates.")
