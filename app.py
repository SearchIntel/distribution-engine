import streamlit as st
import subprocess
import os
from datetime import date
from pathlib import Path

# Config
st.set_page_config(
    page_title="Distribution Engine",
    page_icon="📣",
    layout="wide"
)

# Paths
ROOT = Path(__file__).parent
PROMPTS_DIR = ROOT / "distribution" / "prompts"
OUTPUTS_DIR = ROOT / "distribution" / "outputs"
MASTER_PROMPT = PROMPTS_DIR / "daily_distribution_master.md"

# Load master prompt
@st.cache_data
def load_master_prompt():
    return MASTER_PROMPT.read_text()

# Generate output using Claude CLI
def generate_output(posts_content: str) -> str:
    prompt = load_master_prompt()
    full_prompt = f"{prompt}\n\n----- POSTS START -----\n{posts_content}\n----- POSTS END -----"

    try:
        result = subprocess.run(
            ["claude", "--print", full_prompt],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Request timed out (5 min limit)"
    except FileNotFoundError:
        return "Error: Claude CLI not found. Make sure it's installed and in your PATH."

# Save output
def save_output(content: str) -> Path:
    today = date.today().isoformat()
    output_dir = OUTPUTS_DIR / today
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "daily.md"
    output_file.write_text(content)

    # Create latest.md symlink
    latest = OUTPUTS_DIR / "latest.md"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(output_file)

    return output_file

# UI
st.title("📣 Distribution Engine")
st.caption("LinkedIn content engine for senior marketing leaders")

# Template reference
with st.expander("📋 Paste template (copy this format)"):
    st.code("""--- POST 1 ---
Author:
Role (if obvious):
Why I saved it:
Post text:
[paste the post here]

--- POST 2 ---
Author:
Role:
Why I saved it:
Post text:
[paste]""", language=None)

# Main input
st.subheader("Paste your LinkedIn posts")
posts_input = st.text_area(
    "Posts",
    height=300,
    placeholder="Paste 6-8 LinkedIn posts using the template above...",
    label_visibility="collapsed"
)

# Generate button
col1, col2 = st.columns([1, 4])
with col1:
    generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)

# Output
if generate_btn:
    if not posts_input.strip():
        st.error("Paste some posts first!")
    else:
        with st.spinner("Generating your daily briefing..."):
            output = generate_output(posts_input)

            if output.startswith("Error:"):
                st.error(output)
            else:
                # Save output
                output_path = save_output(output)
                st.success(f"Saved to: {output_path}")

                # Store in session state for display
                st.session_state.output = output

# Display output if exists
if "output" in st.session_state:
    st.divider()
    st.subheader("📄 Today's Output")

    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Full Output", "Comments Only", "Posts Only"])

    with tab1:
        st.markdown(st.session_state.output)

    with tab2:
        # Extract comments section
        output = st.session_state.output
        if "B) Comment Sniper" in output:
            start = output.find("B) Comment Sniper")
            end = output.find("C) Post Factory") if "C) Post Factory" in output else len(output)
            st.markdown(output[start:end])
        else:
            st.info("No comments section found")

    with tab3:
        # Extract posts section
        output = st.session_state.output
        if "C) Post Factory" in output:
            start = output.find("C) Post Factory")
            st.markdown(output[start:])
        else:
            st.info("No posts section found")

    # Copy button
    st.download_button(
        "📥 Download as Markdown",
        st.session_state.output,
        file_name=f"distribution-{date.today().isoformat()}.md",
        mime="text/markdown"
    )

# Footer
st.divider()
st.caption("Tip: Save posts to Apple Notes throughout the day, then paste them all here in one go.")
