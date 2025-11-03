import io
import json
import mimetypes
from typing import Optional, Tuple

import streamlit as st

try:
    import requests
except ImportError:
    requests = None  # We'll show a hint in the UI


# --------------------------
# Page config and base styles
# --------------------------
st.set_page_config(
    page_title="Glaucoma Agent",
    page_icon="🧠",
    layout="centered"
)

PRIMARY_URL_DEFAULT = "https://dominant-usually-oyster.ngrok-free.app"

st.markdown(
    """
    <style>
      .card {
        padding: 1rem 1.25rem;
        border: 1px solid rgba(49,51,63,0.2);
        border-radius: 12px;
        background: linear-gradient(180deg, rgba(250,250,250,0.9) 0%, rgba(245,245,245,0.8) 100%);
      }
      .status-badge {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.9rem;
      }
      .badge-green { background: #DCFCE7; color: #166534; }
      .badge-red { background: #FEE2E2; color: #991B1B; }
      .badge-amber { background: #FEF3C7; color: #92400E; }
      .subtle { color: #6b7280; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------
# Sidebar configuration
# --------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    server_url = st.text_input(
        "Colab Server URL",
        value=st.session_state.get("server_url", PRIMARY_URL_DEFAULT),
        help="Base URL to your Flask backend exposing /predict (e.g. via ngrok).",
    )
    st.session_state["server_url"] = server_url.strip()

    st.caption(
        "Backend must expose POST /predict accepting form-data file under key 'image' and return JSON with classification, detail, ratio, and annotated_image_url."
    )


# --------------------------
# Helpers
# --------------------------
def classification_badge(text: str) -> str:
    t = (text or "").lower().strip()
    if "non" in t:
        cls = "badge-green"
    elif "suspect" in t:
        cls = "badge-amber"
    else:
        cls = "badge-red"
    return f'<span class="status-badge {cls}">{text}</span>'


def infer_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def post_predict(
    base_url: str, file_name: str, file_bytes: bytes, timeout_s: int = 120
) -> Tuple[Optional[dict], Optional[str]]:
    """Call the backend /predict endpoint with the uploaded image.

    Returns: (json_data, error_message)
    """
    if requests is None:
        return None, "Python 'requests' package is not installed. Run: pip install -r requirements.txt"

    url = base_url.rstrip("/") + "/predict"
    files = {
        "image": (file_name, io.BytesIO(file_bytes), infer_mime(file_name)),
    }
    try:
        resp = requests.post(url, files=files, timeout=timeout_s)
    except requests.exceptions.RequestException as e:
        return None, f"Failed to reach server: {e}"

    try:
        data = resp.json()
    except Exception:
        data = None

    if not resp.ok:
        # Prefer server-provided error detail
        if isinstance(data, dict) and data.get("error"):
            return None, f"{data.get('error')}\nDetail: {data.get('detail', 'N/A')}"
        return None, f"Server returned HTTP {resp.status_code}"

    if not isinstance(data, dict):
        return None, "Unexpected response from server (not JSON object)."

    return data, None


# --------------------------
# Main UI
# --------------------------
st.title("👁️ Glaucoma Agent")
st.caption("Upload a retinal fundus image to receive an automated analysis, including CDR and an annotated visualization.")

uploaded = st.file_uploader(
    "Upload fundus image", type=["png", "jpg", "jpeg"], accept_multiple_files=False
)

analyze_col, info_col = st.columns([1, 2])
with analyze_col:
    analyze = st.button("🔍 Analyze", type="primary", disabled=uploaded is None)
with info_col:
    st.write("")
    st.markdown("<span class='subtle'>Accepted formats: PNG, JPG. Typical processing time: a few seconds.</span>", unsafe_allow_html=True)

left, right = st.columns(2)

if uploaded is not None:
    # Show original preview
    with left:
        st.subheader("Original image")
        st.image(uploaded, caption=uploaded.name, use_container_width=True)

result_container = st.container()

if analyze and uploaded is not None:
    if not server_url:
        st.error("Please provide a valid Colab Server URL in the sidebar.")
    else:
        with st.spinner("Contacting Glaucoma Agent…"):
            raw_bytes = uploaded.getvalue()
            data, err = post_predict(server_url, uploaded.name, raw_bytes)

        if err:
            st.error(err)
        else:
            # Expect keys: classification, detail, ratio, annotated_image_url
            classification = data.get("classification") or data.get("final_classification")
            detail = data.get("detail") or data.get("details")
            ratio = data.get("ratio") or data.get("cdr")
            annotated_url = data.get("annotated_image_url")

            # Normalize ratio
            try:
                ratio_val = float(ratio) if ratio is not None else None
            except Exception:
                ratio_val = None

            with result_container:
                st.subheader("Results")

                # Top summary card
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    cols = st.columns([2, 1])
                    with cols[0]:
                        st.markdown(
                            f"Classification: {classification_badge(classification or 'Unknown')}",
                            unsafe_allow_html=True,
                        )
                        if detail:
                            st.write(detail)
                    with cols[1]:
                        if ratio_val is not None:
                            st.metric("Cup-to-Disc Ratio", f"{ratio_val:.2f}")
                        else:
                            st.metric("Cup-to-Disc Ratio", "—")
                    st.markdown("</div>", unsafe_allow_html=True)

                st.divider()

                # Visualizations: Annotated vs Original
                a_col, b_col = st.columns(2)
                with a_col:
                    st.subheader("Annotated image")
                    if isinstance(annotated_url, str) and annotated_url.startswith("http"):
                        st.image(annotated_url, caption="Server-provided annotation", use_container_width=True)
                    else:
                        st.warning("Annotated image not available from server.")

                with b_col:
                    st.subheader("Original image (repeated)")
                    if uploaded is not None:
                        st.image(uploaded, use_container_width=True)

                with st.expander("Advanced • Raw response"):
                    st.json(data)

elif uploaded is None:
    st.info("Upload a fundus image to begin.")


# Guidance when requests isn't available
if requests is None:
    st.warning(
        "'requests' package not found. Please run `pip install -r requirements.txt` and restart the app.",
        icon="⚠️",
    )

