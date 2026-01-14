import streamlit as st
import anthropic
import re
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

# Generate output using Anthropic API
def generate_output(posts_content: str) -> str:
    prompt = load_master_prompt()
    full_prompt = f"{prompt}\n\n----- POSTS START -----\n{posts_content}\n----- POSTS END -----"

    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        return message.content[0].text
    except anthropic.APIError as e:
        return f"Error: API error - {e}"
    except Exception as e:
        return f"Error: {e}"

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

# Extract sections from output
def extract_section(text: str, start_marker: str, end_marker: str = None) -> str:
    if start_marker not in text:
        return ""
    start = text.find(start_marker)
    if end_marker and end_marker in text:
        end = text.find(end_marker)
        return text[start:end].strip()
    return text[start:].strip()

def extract_post_a(text: str) -> str:
    match = re.search(r'1\) LinkedIn Post A.*?\n\[post\]\n?(.*?)(?=\n2\) LinkedIn Post B|\n\*\*2\))', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Alternative pattern
    match = re.search(r'LinkedIn Post A.*?Structure:.*?\n(.*?)(?=\n.*?LinkedIn Post B|\n\*\*2\))', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_post_b(text: str) -> str:
    match = re.search(r'2\) LinkedIn Post B.*?\n\[post\]\n?(.*?)(?=\n3\) Post to Publish|\n\*\*3\))', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_talk_track(text: str) -> str:
    match = re.search(r'6\) Talk Track.*?One-liner:(.*?)(?=\nB\) Comment Sniper|\n\*\*B\))', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_comments(text: str) -> str:
    match = re.search(r'2\) Draft Comments.*?Format:\n?(.*?)(?=\nC\) Post Factory|\n\*\*C\))', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

# Check for potential fabrication (numbers not in input)
def check_fabrication(output: str, input_text: str) -> list:
    warnings = []
    # Find percentages and fractions in output
    output_numbers = set(re.findall(r'\d+%|\d+/\d+|\d+ out of \d+', output))
    input_numbers = set(re.findall(r'\d+%|\d+/\d+|\d+ out of \d+', input_text))

    fabricated = output_numbers - input_numbers
    if fabricated:
        warnings.append(f"⚠️ Possible fabrication detected: {', '.join(fabricated)} — not found in your input")

    return warnings

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
    st.info("💡 Aim for 6-10 posts across: technical AI-search people, agency operators, brand-side leaders, and one contrarian hot take.")

# Main input
st.subheader("Paste LinkedIn posts (text, not URLs)")
posts_input = st.text_area(
    "Posts",
    height=300,
    placeholder="Paste 6-10 LinkedIn posts using the template above.\n\nDon't paste URLs — LinkedIn blocks fetching. Copy the actual post text.",
    label_visibility="collapsed"
)

# Generate button
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)
with col2:
    if st.button("🗑️ Clear", use_container_width=True):
        if "output" in st.session_state:
            del st.session_state.output
        st.rerun()

# Output
if generate_btn:
    if not posts_input.strip():
        st.error("Paste some posts first!")
    elif "--- POST" not in posts_input:
        st.warning("Use the template format: --- POST 1 ---, --- POST 2 ---, etc.")
    else:
        with st.spinner("Generating your daily briefing..."):
            output = generate_output(posts_input)

            if output.startswith("Error:"):
                st.error(output)
            else:
                # Save output
                output_path = save_output(output)
                st.success(f"Saved to: {output_path}")

                # Check for fabrication
                warnings = check_fabrication(output, posts_input)
                for warning in warnings:
                    st.warning(warning)

                # Store in session state for display
                st.session_state.output = output
                st.session_state.input = posts_input

# Display output if exists
if "output" in st.session_state:
    st.divider()
    st.subheader("📄 Today's Output")

    output = st.session_state.output

    # Quick copy section
    st.markdown("### ⚡ Quick Copy")
    copy_cols = st.columns(4)

    with copy_cols[0]:
        post_a = extract_post_a(output)
        if post_a:
            st.text_area("Post A", post_a, height=150, key="post_a_copy")

    with copy_cols[1]:
        post_b = extract_post_b(output)
        if post_b:
            st.text_area("Post B", post_b, height=150, key="post_b_copy")

    with copy_cols[2]:
        talk_track = extract_talk_track(output)
        if talk_track:
            st.text_area("Talk Track", talk_track, height=150, key="talk_track_copy")

    with copy_cols[3]:
        comments = extract_comments(output)
        if comments:
            # Get first 5 comments
            comment_lines = comments.split("Comment ")[:6]
            top_comments = "Comment ".join(comment_lines[1:6]) if len(comment_lines) > 1 else comments[:500]
            st.text_area("Top 5 Comments", top_comments, height=150, key="comments_copy")

    st.caption("💡 Click in any box above, Cmd+A to select all, Cmd+C to copy")

    st.divider()

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Full Output", "Signal Harvester", "Comments", "Posts & DMs"])

    with tab1:
        st.markdown(output)

    with tab2:
        if "A) Signal Harvester" in output:
            section = extract_section(output, "A) Signal Harvester", "B) Comment Sniper")
            st.markdown(section)
        else:
            st.info("No Signal Harvester section found")

    with tab3:
        if "B) Comment Sniper" in output:
            section = extract_section(output, "B) Comment Sniper", "C) Post Factory")
            st.markdown(section)
        else:
            st.info("No Comment Sniper section found")

    with tab4:
        if "C) Post Factory" in output:
            section = extract_section(output, "C) Post Factory")
            st.markdown(section)
        else:
            st.info("No Post Factory section found")

    # Download button
    st.divider()
    st.download_button(
        "📥 Download Full Briefing",
        output,
        file_name=f"distribution-{date.today().isoformat()}.md",
        mime="text/markdown"
    )

# Footer
st.divider()
st.caption("Tip: Save posts to Apple Notes throughout the day, then paste them all here in one go.")
