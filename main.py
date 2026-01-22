# main.py (UPDATED - Added File Upload Feature)
import streamlit as st
from post_generator import (
    generate_post,
    generate_multi_tone_posts,
    generate_multi_model_posts,
)
from file_handler import process_uploaded_file, create_file_based_prompt  # NEW IMPORT
import json
import ast
import html
import re
from datetime import datetime
import urllib.parse

# ---- PAGE CONFIG ----
st.set_page_config(page_title="LinkGen AI", layout="centered")

# ---- SESSION STATE INITIALIZATION ----
if 'post_history' not in st.session_state:
    st.session_state.post_history = []
if 'current_post' not in st.session_state:
    st.session_state.current_post = None
if 'last_inputs' not in st.session_state:
    st.session_state.last_inputs = {}
if 'multi_tone_posts' not in st.session_state:
    st.session_state.multi_tone_posts = {}
if 'show_multi_tone' not in st.session_state:
    st.session_state.show_multi_tone = False
if 'multi_model_posts' not in st.session_state:
    st.session_state.multi_model_posts = {}
if 'show_multi_model' not in st.session_state:
    st.session_state.show_multi_model = False
# NEW: File upload state
if 'uploaded_file_content' not in st.session_state:
    st.session_state.uploaded_file_content = None
if 'file_info' not in st.session_state:
    st.session_state.file_info = None

# ---- CUSTOM STYLING ----
st.markdown("""
    <style>
        body {
            background-color: #0A2342;
            color: white;
        }
        .main {
            background-color: #0A2342;
        }
        .stSelectbox label, .stTextArea label, .stRadio label, .stCheckbox label, p, h2, h3, h4, h5, h6 {
            color: white !important;
        }
        .stTextArea textarea {
            color: black !important;
            background-color: white !important;
            border: 1px solid #ffffff !important;
        }
        .stSelectbox div[data-baseweb="select"] {
            color: black !important;
            background-color: white !important;
            border: 1px solid white !important;
            border-radius: 5px !important;
        }
        /* ===== UNIFIED BUTTON STYLING FIX ===== */
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        button[kind="primary"],
        button[kind="secondary"],
        button[role="button"],
        button[data-baseweb="button"],
        .css-1emrehy.edgvbvh3,
        .css-1n543e5.edgvbvh3 {
            background-color: #007bff !important;
            color: white !important;
            border-radius: 10px !important;
            height: 45px !important;
            width: 100% !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            border: 1px solid #ffffff !important;
            transition: 0.25s ease !important;
            padding: 0 10px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* Hover effect for all buttons */
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        button[role="button"]:hover,
        button[data-baseweb="button"]:hover,
        .css-1emrehy.edgvbvh3:hover,
        .css-1n543e5.edgvbvh3:hover {
            background-color: #0056b3 !important;
            transform: scale(1.02) !important;
            border: 1px solid #cfe2ff !important;
        }

        /* Align buttons in columns */
        div[data-testid="column"] {
            padding: 0 6px !important;
        }

        .card {
            background-color: #0d2b52;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 2px 6px rgba(255,255,255,0.1);
            margin-top: 20px;
        }
        .note {
            text-align: center;
            font-size: 14px;
            color: #cfd8dc;
            font-style: italic;
            margin-bottom: 10px;
        }
        .hashtag { color: #9ed2ff; margin-right:8px; }
        .char-counter {
            text-align: right;
            font-size: 13px;
            color: #9ed2ff;
            margin-top: 5px;
        }
        .char-counter.warning { color: #ff6b6b; font-weight: bold; }
        .tone-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .tone-professional { background-color: #2c5aa0; color: white; }
        .tone-casual { background-color: #f39c12; color: white; }
        .tone-inspirational { background-color: #e74c3c; color: white; }
        /* NEW: File upload styling */
        .file-info {
            background-color: #1e4976;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
        }
        .file-preview {
            background-color: #0d2b52;
            padding: 15px;
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
            font-size: 13px;
            color: #cfd8dc;
        }
    </style>
""", unsafe_allow_html=True)



# ---- TITLE ----
st.markdown("<h1 style='text-align: center; color: white;'>⚡ LinkGen AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #9ed2ff; font-weight: 500;'>Write It Once. See It Through Every Model and Tone.</p>", unsafe_allow_html=True)

# ---- NOTE ----
st.markdown("<p class='note'>Note: The selected topic will be used only if you leave the description box empty.</p>", unsafe_allow_html=True)

# ---- DROPDOWNS ----
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.selectbox(
        "Select Topic",
        ["All", "Motivation", "Leadership", "AI", "Productivity", "Career Growth", "Teamwork", "Communication", "Technology", "Networking"]
    )
with col2:
    length = st.selectbox("Select Post Length", ["Short", "Medium", "Long"])
with col3:
    language = st.selectbox("Select Language", ["English", "Kannada", "Hindi"])

# ---- MULTI-TONE CHECKBOX ----
use_multi_tone = st.checkbox(
    "Generate Multiple Tones (3 variations)", 
    value=False,
    help="Generate 3 different versions: Professional, Casual, and Inspirational"
)

# ---- MULTI-MODEL CHECKBOX ----
use_multi_model = st.checkbox(
    "Compare Multi-Models (3 models)", 
    value=False,
    help="Generate 3 different model variants: Llama-3.1-8B, Llama-3.1-70B, and Groq"
)

# ---- NEW: FILE UPLOAD SECTION ----
st.markdown("<hr style='margin: 20px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color: white;'>📄 Upload File (Optional)</h3>", unsafe_allow_html=True)
st.markdown("<p style='color: #9ed2ff; font-size: 14px;'>Upload a resume, presentation, or document to generate a LinkedIn post based on its content</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose a file (PDF, DOCX, PPTX, TXT)",
    type=['pdf', 'docx', 'pptx', 'txt'],
    help="Max file size: 10MB"
)

# Process uploaded file
if uploaded_file is not None:
    with st.spinner("Processing file..."):
        file_result = process_uploaded_file(uploaded_file)
        
        if file_result.get("error"):
            st.error(f"❌ {file_result['error']}")
            st.session_state.uploaded_file_content = None
            st.session_state.file_info = None
        else:
            st.session_state.uploaded_file_content = file_result["content"]
            st.session_state.file_info = {
                "filename": file_result["filename"],
                "file_type": file_result["file_type"]
            }
            
            # Display file info
            st.markdown(
                f"<div class='file-info'>"
                f"<strong>✅ File Processed:</strong> {file_result['filename']}<br>"
                f"<strong>Content Length:</strong> {len(file_result['content'])} characters<br>"
                f"<small style='color: #9ed2ff;'>The content will be used to generate your LinkedIn post</small>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            # Show preview of extracted content
            with st.expander("📖 Preview Extracted Content", expanded=False):
                preview_text = file_result["content"][:500] + "..." if len(file_result["content"]) > 500 else file_result["content"]
                st.markdown(f"<div class='file-preview'>{html.escape(preview_text)}</div>", unsafe_allow_html=True)
            
            # Option to clear file
            if st.button("🗑️ Clear Uploaded File"):
                st.session_state.uploaded_file_content = None
                st.session_state.file_info = None
                st.rerun()

elif st.session_state.uploaded_file_content:
    # Show existing file info if file was uploaded before
    st.markdown(
        f"<div class='file-info'>"
        f"<strong>✅ Using File:</strong> {st.session_state.file_info['filename']}<br>"
        f"<strong>Content Length:</strong> {len(st.session_state.uploaded_file_content)} characters"
        f"</div>",
        unsafe_allow_html=True
    )
    if st.button("🗑️ Clear Uploaded File"):
        st.session_state.uploaded_file_content = None
        st.session_state.file_info = None
        st.rerun()

st.markdown("<hr style='margin: 20px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)

# ---- CUSTOM PROMPT BOX ----
st.markdown('<div class="card"><strong style="font-size:20px;color:#ffffff">Describe the post you want (optional)</strong></div>', unsafe_allow_html=True)
st.write("Example: I completed my first internship at Google – write a short celebratory post with two lessons learned.")
custom_prompt = st.text_area("Type your custom prompt (optional)", value="", height=100)

# -----------------------
# Helper: clean & extract result
# -----------------------
def extract_and_clean(raw_result):
    """
    Accept various shapes from generate_post and clean them
    """
    out = {"post": "", "hashtags": [], "engagement": None}

    if isinstance(raw_result, dict):
        out["post"] = raw_result.get("post") or raw_result.get("text") or raw_result.get("content") or ""
        tags = raw_result.get("hashtags", raw_result.get("tags", []))
        if isinstance(tags, str):
            out["hashtags"] = [t.strip() for t in tags.split(",") if t.strip()]
        elif isinstance(tags, list):
            out["hashtags"] = tags
        out["engagement"] = raw_result.get("engagement", raw_result.get("score"))
        out["tone"] = raw_result.get("tone", "")
        return clean_text_output(out)

    if isinstance(raw_result, str):
        s = raw_result.strip()
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                return extract_and_clean(parsed)
        except Exception:
            pass
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, dict):
                return extract_and_clean(parsed)
        except Exception:
            pass
        try:
            unescaped = bytes(s, "utf-8").decode("unicode_escape")
        except Exception:
            unescaped = s

        if "{" in unescaped and "}" in unescaped:
            start = unescaped.find("{")
            end = unescaped.rfind("}") + 1
            try:
                piece = unescaped[start:end]
                parsed = json.loads(piece)
                if isinstance(parsed, dict):
                    return extract_and_clean(parsed)
            except Exception:
                pass

        out["post"] = unescaped
        return clean_text_output(out)

    out["post"] = str(raw_result)
    return clean_text_output(out)

def clean_text_output(out):
    post = out.get("post", "") or ""
    post = post.replace("\\/", "/")
    post = post.replace("\\n", "\n")
    post = post.replace("\\", "")

    post = re.sub(r'\.{3,}', '...', post)
    post = re.sub(r'-{3,}', '---', post)
    post = re.sub(r'\s{3,}', '  ', post)

    post = post.replace("\r\n", "\n").replace("\r", "\n")
    post = post.strip(" \n\r\t\"'")
    safe = html.escape(post)

    paragraphs = [p.strip() for p in safe.split("\n\n") if p.strip()]
    newline_token = '\n'
    if paragraphs:
        html_paragraphs = "".join(
            "<p style='margin:8px 0; line-height:1.6;'>{}</p>".format(p.replace(newline_token, ' '))
            for p in paragraphs
        )
    else:
        html_paragraphs = "<p style='margin:8px 0; line-height:1.6;'>{}</p>".format(safe)

    out["post_html"] = html_paragraphs
    tags = out.get("hashtags") or []
    clean_tags = []
    if isinstance(tags, str):
        clean_tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif isinstance(tags, list):
        for t in tags:
            if isinstance(t, str):
                clean_tags.append(t.strip())
            else:
                clean_tags.append(str(t))
    out["hashtags"] = clean_tags
    return out

# -----------------------
# BUTTON AND GENERATION LOGIC
# -----------------------
col_gen, col_clear = st.columns([3, 1])
with col_gen:
    generate_clicked = st.button("Generate Post")
with col_clear:
    if st.button("Clear All"):
        st.session_state.current_post = None
        st.session_state.last_inputs = {}
        st.session_state.multi_tone_posts = {}
        st.session_state.show_multi_tone = False
        st.session_state.multi_model_posts = {}
        st.session_state.show_multi_model = False
        st.session_state.uploaded_file_content = None
        st.session_state.file_info = None
        st.rerun()

def build_prompt(base_prompt, length_hint, language_hint):
    parts = []
    if length_hint:
        if length_hint.lower() == "short":
            parts.append("Keep it short and concise (about 2-3 short paragraphs or ~40-80 words).")
        elif length_hint.lower() == "medium":
            parts.append("Write a medium-length LinkedIn-style post (about 3-5 short paragraphs or ~100-160 words).")
        elif length_hint.lower() == "long":
            parts.append("Write a long, detailed LinkedIn-style post (more depth, 5+ paragraphs or ~200+ words).")
    if language_hint:
        parts.append("Write the post in {}.".format(language_hint))
    parts.append("Write in a natural LinkedIn voice (professional, clear).")

    instruction = " ".join(parts)
    final_prompt = base_prompt.strip() + "\n\n" + instruction
    return final_prompt

if generate_clicked:
    spinner_text = "Generating your post..."
    if use_multi_tone and use_multi_model:
        spinner_text = "Generating multi-tone + multi-model results... this may take 10-15 seconds ⏳"
    elif use_multi_tone:
        spinner_text = "Generating 3 tone variations... This may take 5-10 seconds ⏳"
    elif use_multi_model:
        spinner_text = "Generating 3 model comparisons... This may take 5-10 seconds ⏳"

    with st.spinner(spinner_text):
        # NEW: Check if file content should be used
        if st.session_state.uploaded_file_content:
            # Use file content to generate prompt
            base = create_file_based_prompt(
                st.session_state.uploaded_file_content,
                st.session_state.file_info.get("file_type", "document")
            )
        elif custom_prompt.strip():
            base = custom_prompt.strip()
        else:
            if topic == "All":
                base = "Generate a LinkedIn post about professional growth and career development."
            else:
                base = f"Generate a LinkedIn post about {topic}."

        prompt_input = build_prompt(base, length, language)
        st.session_state.last_inputs = {
            'prompt': prompt_input,
            'length': length,
            'language': language,
            'topic': topic,
            'custom_prompt': custom_prompt,
            'use_multi_tone': use_multi_tone,
            'use_multi_model': use_multi_model,
            'used_file': st.session_state.file_info.get("filename") if st.session_state.file_info else None
        }

        # FIXED: Clear previous results first
        st.session_state.show_multi_model = False
        st.session_state.show_multi_tone = False
        st.session_state.multi_model_posts = {}
        st.session_state.multi_tone_posts = {}

        # MULTI-MODEL BRANCH (sequential generation)
        if use_multi_model:
            st.session_state.show_multi_model = True
            multi_model_res = generate_multi_model_posts(
                topic=prompt_input,
                length=length,
                language=language,
                custom_prompt=custom_prompt,
                use_parallel=False
            )
            st.session_state.multi_model_posts = {}
            for model_name, res in multi_model_res.items():
                st.session_state.multi_model_posts[model_name] = extract_and_clean(res)
            if st.session_state.multi_model_posts:
                first_model = list(st.session_state.multi_model_posts.keys())[0]
                st.session_state.current_post = st.session_state.multi_model_posts[first_model]

        # MULTI-TONE BRANCH (FIXED - 3 tones)
        if use_multi_tone:
            st.session_state.show_multi_tone = True
            multi_results = generate_multi_tone_posts(
                topic=prompt_input,
                length=length,
                language=language,
                custom_prompt=custom_prompt,
                use_parallel=False
            )
            st.session_state.multi_tone_posts = {}
            for tone_name, result in multi_results.items():
                st.session_state.multi_tone_posts[tone_name] = extract_and_clean(result)
            if st.session_state.multi_tone_posts:
                first_tone = list(st.session_state.multi_tone_posts.keys())[0]
                st.session_state.current_post = st.session_state.multi_tone_posts[first_tone]

        # If neither comparison selected, single generate
        if not use_multi_tone and not use_multi_model:
            result = generate_post(prompt_input, length, language, custom_prompt=custom_prompt)
            parsed = extract_and_clean(result)
            st.session_state.current_post = parsed

            history_item = {
                'post': parsed,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'inputs': st.session_state.last_inputs.copy()
            }
            st.session_state.post_history.insert(0, history_item)
            if len(st.session_state.post_history) > 5:
                st.session_state.post_history = st.session_state.post_history[:5]

# -----------------------
# MULTI-MODEL DISPLAY SECTION
# -----------------------
if st.session_state.show_multi_model and st.session_state.multi_model_posts:
    st.markdown("<hr style='margin: 30px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:white; text-align:center;'>Multi-Model Comparison</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#9ed2ff; margin-bottom:20px;'>Compare how different model variants render the same prompt.</p>", unsafe_allow_html=True)

    model_names = list(st.session_state.multi_model_posts.keys())
    if model_names:
        model_tabs = st.tabs(model_names)
        for idx, model_name in enumerate(model_names):
            with model_tabs[idx]:
                model_post = st.session_state.multi_model_posts.get(model_name, {})
                if model_post.get("error"):
                    st.error(f"Error generating for {model_name}: {model_post.get('post', 'Unknown error')}")
                    continue

                post_text = model_post.get("post", "")
                tags = model_post.get("hashtags", [])
                full_text = f"{post_text}\n\n{' '.join(tags)}".strip()

                char_count = len(full_text)
                counter_class = "char-counter warning" if char_count > 3000 else "char-counter"
                st.markdown(f"<div class='{counter_class}'>Characters: {char_count}/3000</div>", unsafe_allow_html=True)

                st.markdown("<p style='color:#9ed2ff; font-size:13px; margin-top:10px;'>Edit below:</p>", unsafe_allow_html=True)
                edited_model_post = st.text_area(f"{model_name} output", value=full_text, height=220, key=f"model_{model_name}_edit", label_visibility="collapsed")

                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.download_button(
                        label="Download",
                        data=edited_model_post,
                        file_name=f"post_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"dl_model_{model_name}"
                    )
                with col_b:
                    if st.button(f"Copy", key=f"copy_model_{model_name}", use_container_width=True):
                        st.code(edited_model_post)
                        st.success(f"{model_name} post ready to copy!")
                with col_c:
                    encoded = urllib.parse.quote(edited_model_post[:1000])
                    linkedin_url = f"https://www.linkedin.com/feed/?shareActive=true&text={encoded}"
                    if st.button(f"Share", key=f"share_model_{model_name}", use_container_width=True):
                        st.info(f"[Click here to share on LinkedIn]({linkedin_url})")
                with col_d:
                    if st.button(f"Use This", key=f"use_model_{model_name}", use_container_width=True):
                        st.session_state.current_post = model_post
                        st.session_state.show_multi_model = False
                        history_item = {
                            'post': model_post,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'inputs': st.session_state.last_inputs.copy()
                        }
                        st.session_state.post_history.insert(0, history_item)
                        if len(st.session_state.post_history) > 5:
                            st.session_state.post_history = st.session_state.post_history[:5]
                        st.rerun()

                st.markdown("<hr style='margin: 15px 0; border: 1px solid #ffffff22;'>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='color:#9ed2ff;'>{model_name} Preview</h4>", unsafe_allow_html=True)
                st.markdown(model_post.get("post_html", ""), unsafe_allow_html=True)

                if tags:
                    tags_html = " ".join(f"<span class='hashtag'>{html.escape(t)}</span>" for t in tags)
                    st.markdown(f"<div style='margin-top:10px'><strong style='color:#fff'>Hashtags: </strong>{tags_html}</div>", unsafe_allow_html=True)

                eng = model_post.get("engagement")
                if eng:
                    st.markdown(f"<div style='margin-top:8px;color:#dfeeff;'><strong>Engagement estimate:</strong> {html.escape(str(eng))}</div>", unsafe_allow_html=True)

# -----------------------
# MULTI-TONE DISPLAY (FIXED - 3 tones)
# -----------------------
if st.session_state.show_multi_tone and st.session_state.multi_tone_posts:
    st.markdown("<hr style='margin: 30px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:white; text-align:center;'>Multi-Tone Variations</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#9ed2ff; margin-bottom:20px;'>Choose the tone that best fits your audience and message</p>", unsafe_allow_html=True)

    tone_tabs = st.tabs([
        "Professional",
        "Casual",
        "Inspirational"
    ])
    tone_names = ["Professional", "Casual", "Inspirational"]
    tone_classes = ["professional", "casual", "inspirational"]

    for idx, (tab, tone_name, tone_class) in enumerate(zip(tone_tabs, tone_names, tone_classes)):
        with tab:
            tone_post = st.session_state.multi_tone_posts.get(tone_name, {})
            if tone_post.get("error"):
                st.error(f"Error generating this tone: {tone_post.get('post', 'Unknown error')}")
                continue

            st.markdown(f"<span class='tone-badge tone-{tone_class}'>{tone_name.upper()}</span>", unsafe_allow_html=True)
            post_text = tone_post.get("post", "")
            tags = tone_post.get("hashtags", [])
            full_text = f"{post_text}\n\n{' '.join(tags)}".strip()

            char_count = len(full_text)
            counter_class = "char-counter warning" if char_count > 3000 else "char-counter"
            st.markdown(f"<div class='{counter_class}'>Characters: {char_count}/3000</div>", unsafe_allow_html=True)

            st.markdown("<p style='color:#9ed2ff; font-size:13px; margin-top:10px;'>Edit below:</p>", unsafe_allow_html=True)
            edited_tone_post = st.text_area(
                f"{tone_name} Version",
                value=full_text,
                height=200,
                key=f"tone_{tone_name}_edit",
                label_visibility="collapsed"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.download_button(
                    label="Download",
                    data=edited_tone_post,
                    file_name=f"linkedin_{tone_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key=f"download_{tone_name}",
                    use_container_width=True
                )

            with col2:
                if st.button(f"Copy", key=f"copy_{tone_name}", use_container_width=True):
                    st.code(edited_tone_post, language=None)
                    st.success(f"{tone_name} post ready to copy!")

            with col3:
                encoded_text = urllib.parse.quote(edited_tone_post[:1000])
                linkedin_url = f"https://www.linkedin.com/feed/?shareActive=true&text={encoded_text}"
                if st.button(f"Share", key=f"share_{tone_name}", use_container_width=True):
                    st.info(f"[Click here to share on LinkedIn]({linkedin_url})")

            with col4:
                if st.button(f"Use This", key=f"use_{tone_name}", use_container_width=True):
                    st.session_state.current_post = tone_post
                    st.session_state.show_multi_tone = False

                    history_item = {
                        'post': tone_post,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'inputs': st.session_state.last_inputs.copy()
                    }
                    st.session_state.post_history.insert(0, history_item)
                    if len(st.session_state.post_history) > 5:
                        st.session_state.post_history = st.session_state.post_history[:5]

                    st.rerun()

            st.markdown("<hr style='margin: 15px 0; border: 1px solid #ffffff22;'>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='color:#9ed2ff;'>{tone_name} Preview</h4>", unsafe_allow_html=True)
            post_html = tone_post.get("post_html", "")
            st.markdown(post_html, unsafe_allow_html=True)

            if tags:
                tags_html = " ".join(f"<span class='hashtag'>{html.escape(t)}</span>" for t in tags)
                st.markdown(f"<div style='margin-top:10px'><strong style='color:#fff'>Hashtags: </strong>{tags_html}</div>", unsafe_allow_html=True)

            eng = tone_post.get("engagement")
            if eng:
                st.markdown(f"<div style='margin-top:8px;color:#dfeeff;'><strong>Engagement estimate:</strong> {html.escape(str(eng))}</div>", unsafe_allow_html=True)

# -----------------------
# SINGLE POST DISPLAY
# -----------------------
if st.session_state.current_post and not st.session_state.show_multi_tone and not st.session_state.show_multi_model:
    st.markdown("<hr style='margin: 30px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:white; text-align:center;'>Generated Post</h2>", unsafe_allow_html=True)
    
    post_text = st.session_state.current_post.get("post", "")
    tags = st.session_state.current_post.get("hashtags", [])
    full_text = f"{post_text}\n\n{' '.join(tags)}".strip()

    char_count = len(full_text)
    counter_class = "char-counter warning" if char_count > 3000 else "char-counter"
    st.markdown(f"<div class='{counter_class}'>Characters: {char_count}/3000</div>", unsafe_allow_html=True)

    st.markdown("<p style='color:#9ed2ff; font-size:13px; margin-top:10px;'>Edit your post below:</p>", unsafe_allow_html=True)
    edited_post = st.text_area("Edit Post", value=full_text, height=250, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Download Post",
            data=edited_post,
            file_name=f"linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col2:
        if st.button("Copy Post", use_container_width=True):
            st.code(edited_post, language=None)
            st.success("Post is ready to copy!")

    with col3:
        encoded_text = urllib.parse.quote(edited_post[:1000])
        linkedin_url = f"https://www.linkedin.com/feed/?shareActive=true&text={encoded_text}"
        if st.button("Share on LinkedIn", use_container_width=True):
            st.info(f"[Click here to share]({linkedin_url})")

    st.markdown("<hr style='margin: 20px 0; border: 1px solid #ffffff22;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#9ed2ff;'>Preview</h3>", unsafe_allow_html=True)
    post_html = st.session_state.current_post.get("post_html", "")
    st.markdown(post_html, unsafe_allow_html=True)

    if tags:
        tags_html = " ".join(f"<span class='hashtag'>{html.escape(t)}</span>" for t in tags)
        st.markdown(f"<div style='margin-top:10px'><strong style='color:#fff'>Hashtags: </strong>{tags_html}</div>", unsafe_allow_html=True)

    eng = st.session_state.current_post.get("engagement")
    if eng:
        st.markdown(f"<div style='margin-top:8px;color:#dfeeff;'><strong>Engagement estimate:</strong> {html.escape(str(eng))}</div>", unsafe_allow_html=True)

# -----------------------
# POST HISTORY SECTION
# -----------------------
if st.session_state.post_history:
    st.markdown("<hr style='margin: 30px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:white; text-align:center;'>Post History</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#9ed2ff; margin-bottom:20px;'>Your last 5 generated posts</p>", unsafe_allow_html=True)

    for idx, item in enumerate(st.session_state.post_history):
        with st.expander(f"Post {idx + 1} - {item['timestamp']}", expanded=False):
            post_data = item['post']
            post_text = post_data.get("post", "")
            tags = post_data.get("hashtags", [])
            
            st.markdown(post_data.get("post_html", ""), unsafe_allow_html=True)
            
            if tags:
                tags_html = " ".join(f"<span class='hashtag'>{html.escape(t)}</span>" for t in tags)
                st.markdown(f"<div style='margin-top:10px'><strong style='color:#fff'>Hashtags: </strong>{tags_html}</div>", unsafe_allow_html=True)
            
            full_text = f"{post_text}\n\n{' '.join(tags)}".strip()
            
            col_h1, col_h2, col_h3 = st.columns(3)
            with col_h1:
                st.download_button(
                    label="Download",
                    data=full_text,
                    file_name=f"linkedin_post_history_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key=f"history_dl_{idx}",
                    use_container_width=True
                )
            with col_h2:
                if st.button("Copy", key=f"history_copy_{idx}", use_container_width=True):
                    st.code(full_text, language=None)
                    st.success("Post ready to copy!")
            with col_h3:
                if st.button("Reuse", key=f"history_reuse_{idx}", use_container_width=True):
                    st.session_state.current_post = post_data
                    st.session_state.show_multi_tone = False
                    st.session_state.show_multi_model = False
                    st.rerun()

# -----------------------
# FOOTER
# -----------------------
st.markdown("<hr style='margin: 30px 0; border: 1px solid #ffffff33;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#9ed2ff; font-size:12px;'>💡 Tip: For best results, be specific in your custom prompt. Mention key points, achievements, or the message you want to convey.</p>", unsafe_allow_html=True)