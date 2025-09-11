import streamlit as st
import moviepy as mp
from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("🎥 Video to Career Article Generator")

# Language selection
language = st.selectbox("Choose language for article output:", ["English", "Hindi"])

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

# Initialize session state variables
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "article_en" not in st.session_state:
    st.session_state.article_en = None
if "article_hi" not in st.session_state:
    st.session_state.article_hi = None
if "video_processed" not in st.session_state:
    st.session_state.video_processed = False

def process_video(file):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(file.read())
        video_path = temp_video.name

    st.success("✅ Video uploaded successfully!")

    # Extract audio
    st.info("Extracting audio from video...")
    video = mp.VideoFileClip(video_path)
    audio_file = video.audio

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        audio_path = temp_audio.name
        audio_file.write_audiofile(audio_path, codec="mp3", bitrate="64k")

    st.success("✅ Audio extracted and compressed!")

    # Transcribe audio
    st.info("Transcribing audio (this may take some time)...")
    with open(audio_path, "rb") as af:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",  # or "whisper-1"
            file=af
        )

    st.success("✅ Transcription complete!")

    # Generate career article in English
    st.info("Generating structured article from transcript...")
    prompt = f"""
    You are an expert career guide. Based on the following transcript, create an article in this exact format:

    1. What is it?
    2. Education(required degrees, certifications)
    3. Skills (Technical, Soft, Domain-specific)
    5. Positives
    6. Challenges
    7. A Day in the Life

    ⚡ Rules:
    - Assign weightage (%) to each section (total = 100%).
    - Explain briefly how weightage is calculated.
    - Use clear headings and bullet points.
    - only use the information present in the transcript, do not add any extra information if inforation is not available then add information from internet.
    Transcript:
    \"\"\"{transcript.text}\"\"\"
    """

    article_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that formats transcripts into structured career articles."},
            {"role": "user", "content": prompt}
        ]
    )

    article_text = article_response.choices[0].message.content
    st.success("✅ Article generated in English!")

    # Store results in session state
    st.session_state.transcript = transcript.text
    st.session_state.article_en = article_text
    st.session_state.article_hi = None  # Reset Hindi translation cache
    st.session_state.video_processed = True

# Process video only if new file uploaded or first time
if uploaded_file is not None:
    if not st.session_state.video_processed or uploaded_file != st.session_state.get("last_uploaded_file", None):
        process_video(uploaded_file)
        st.session_state.last_uploaded_file = uploaded_file

# If processed, show article based on language
if st.session_state.video_processed:
    if language == "English":
        article_text = st.session_state.article_en
    else:
        # Translate if not cached
        if st.session_state.article_hi is None:
            st.info("Translating article to Hindi...")
            translation_prompt = f"""
            Translate the following article to Hindi. Keep formatting intact (headings, bullet points, weightages etc):

            Article:
            \"\"\"{st.session_state.article_en}\"\"\"
            """
            translation_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a translator that converts English content to Hindi, preserving formatting."},
                    {"role": "user", "content": translation_prompt}
                ]
            )
            st.session_state.article_hi = translation_response.choices[0].message.content
            st.success("✅ Article translated to Hindi!")

        article_text = st.session_state.article_hi

    # Display article
    st.subheader("📄 Generated Article")
    st.markdown(article_text)

    # Download options
    st.download_button(
        label="⬇️ Download Article as TXT",
        data=article_text,
        file_name="article.txt",
        mime="text/plain"
    )

    st.download_button(
        label="⬇️ Download Transcript as TXT",
        data=st.session_state.transcript,
        file_name="transcript.txt",
        mime="text/plain"
    )
