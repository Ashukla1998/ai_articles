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

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(uploaded_file.read())
        video_path = temp_video.name

    st.success("✅ Video uploaded successfully!")

    # Step 1: Extract audio
    st.info("Extracting audio from video...")
    video = mp.VideoFileClip(video_path)
    audio_file = video.audio

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        audio_path = temp_audio.name
        audio_file.write_audiofile(audio_path, codec="mp3", bitrate="64k")

    st.success("✅ Audio extracted and compressed!")

    # Step 2: Transcribe using Whisper
    st.info("Transcribing audio (this may take some time)...")
    with open(audio_path, "rb") as af:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",  # or "whisper-1"
            file=af
        )

    st.success("✅ Transcription complete!")

    # Step 3: Generate career article in English
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

    # Step 4: Translate to Hindi if selected
    if language == "Hindi":
        st.info("Translating article to Hindi...")
        translation_prompt = f"""
        Translate the following article to Hindi. Keep formatting intact (headings, bullet points, weightages etc):

        Article:
        \"\"\"{article_text}\"\"\"
        """

        translation_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a translator that converts English content to Hindi, preserving formatting."},
                {"role": "user", "content": translation_prompt}
            ]
        )

        article_text = translation_response.choices[0].message.content
        st.success("✅ Article translated to Hindi!")

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
        data=transcript.text,
        file_name="transcript.txt",
        mime="text/plain"
    )

