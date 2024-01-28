# Import libraries
import streamlit as st
import os
from supabase import create_client, Client
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import ChatMessage
from py_youtube import Data
import requests
import uuid
import json

from dotenv import load_dotenv
env_path = '../../.env.local'
# import your OpenAI key
# Load the environment variables from the specified .env file
load_dotenv(dotenv_path=env_path)

# Setup Supabase
url: str = os.environ.get("SUPABASE_URL")
print(url)
key: str = os.environ.get("SUPABASE_KEY")
print(key)
supabase: Client = create_client(url, key)

# Set page config & title
st.set_page_config(
    page_title="Podcast Generator", page_icon="ðŸŽ™", initial_sidebar_state="expanded"
)
st.title("ðŸŽ™ Podcast Generator")

# Function to get the summary from the YouTube video
def youtube_summary(url):
    
    # Extract the Youtube ID from the URL
    youtube_id = url.split("=")[1]
    youtube_id = youtube_id.split("&")[0]

    # Check if a summary already exists in Supabase
    response = supabase.table("content_youtube").select("*").eq("youtube_id", youtube_id).execute()

    # If the summary exists, retrieve it from Supabase
    if len(response.data) > 0 and response.data[0]["summary"] is not None:
        id = response.data[0]["id"]
        summary = response.data[0]["summary"]
        overview = response.data[0]["overview"]
        title = response.data[0]["title"]
 
    else:
        # Getting the video transcript
        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
        transcript_text = TextFormatter().format_transcript(transcript)
        st.session_state['youtube_transcript'] = transcript_text

        # Get the video metadata
        youtube_data = Data("https://www.youtube.com/watch?v=" + youtube_id).data()

        # Define output structure
        class Output(BaseModel):
            summary: str = Field(description="A concise summary of the transcript")
            overview: str = Field(description="A one sentence overview of the transcript")
        
        # Set the output parser
        output_parser = JsonOutputParser(pydantic_object=Output)

        # Create prompt for the summary
        prompt = PromptTemplate(
            template="{format_instructions}\n\nYou are a podcast host creating personalised podcasts for users based on their favourite youtube channels.  Provide a concise summary of the main content from the YouTube video transcript, always starting with which channel it is and what the name of the video is. Focus on the essential information, concepts, or ideas presented.  Summarize only the core content, ensuring to capture the key points or topics discussed in a clear and straightforward manner. End by summarising why the listener might want to watch the video in full based on what more they would learn and what value it could add to them:\n\nAuthor:{author}\n\nTitle:{title}\n\nTranscription:{transcription}\n",
            input_variables=["transcription","author","title"],
            partial_variables={"format_instructions": output_parser.get_format_instructions()},
        )

        # Infer the summary
        runnable = prompt | ChatOpenAI(model="gpt-4-1106-preview", temperature=0) | output_parser
        response = runnable.invoke({"transcription": transcript_text, "author": youtube_data["channel_name"], "title": youtube_data["title"]})

        # Save all data to Supabase
        response = supabase.table("content_youtube").insert([{
            "youtube_url": "https://www.youtube.com/watch?v=" + youtube_id,
            "youtube_id": youtube_id,
            "transcript": transcript_text,
            "summary": response["summary"],
            "overview": response["overview"],
            "title": youtube_data["title"],
            "author": youtube_data["channel_name"],
        }]).execute()

        # Set outputs
        id = response.data[0]["id"]
        summary = response.data[0]["summary"]
        overview = response.data[0]["overview"]
        title = response.data[0]["title"]
    
    return {"id": id, "summary": summary, "overview": overview, "title": title}

# Create a function to generate the intro
def podcast_intro(title1, overview1, title2, overview2, title3, overview3, ep1id, ep2id, ep3id):
    
    # Define output structure
    class Output(BaseModel):
        intro: str = Field(description="The intro for the podcast")
        title: str = Field(description="A short title for the podcast")
    
    # Set the output parser
    output_parser = JsonOutputParser(pydantic_object=Output)

    # Create prompt for the summary
    prompt = PromptTemplate(
        template="{format_instructions}\n\nYou are a podcast host creating personalised podcasts for users, called 'My Daily Digest' based on their subscribed youtube channels.  Create an intro for the podcast based on the videos being discussed.  Here is an example:\n\nWelcome to 'My Daily Digest', bringing you a summary of the latest content from your favourite YouTube channels.  Today, we'll discuss the path to AGI, the latest Open AI models, Mixtral's performance and some of the latest AI tools.:\n\nCreate an intro script based on the following video titles and overviews:\n\n{title1}:{overview1}\n\n{title2}:{overview2}\n\n{title3}:{overview3}\n",
        input_variables=["title1", "overview1", "title2", "overview2", "title3", "overview3"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
    )

    # Infer the summary
    runnable = prompt | ChatOpenAI(model="gpt-4-1106-preview", temperature=0) | output_parser
    response = runnable.invoke({"title1": title1, "overview1": overview1, "title2": title2, "overview2": overview2, "title3": title3, "overview3": overview3})

    # Save all data to Supabase
    response = supabase.table("podcast_episode").insert([{
        "intro": response["intro"],
        "title": response["title"],
        "episode1_id": ep1id,
        "episode2_id": ep2id,
        "episode3_id": ep3id,
    }]).execute()

    # Set outputs
    intro = response.data[0]["intro"]
    title = response.data[0]["title"]
    supabase_id = response.data[0]["id"]
    
    # Return the title, intro and supabase id
    return {"title": title, "intro": intro, "supabase_id": supabase_id}

# Function to generate script for the podcast
def generate_script(id):

    # Define the outro
    outro = "Thanks for listening to 'My Daily Digest'. If you wish this show had covered more topics in more depth, you can upgrade to 10 or 20 minute digests which cover even more of favourite channels! Just visit our website, mydailydigest.show"

    # Get the podcast episode details from supabase
    response = supabase.table("podcast_episode").select("*").eq("id", id).execute()

    # Get the summaries for the episodes
    summaries = supabase.table("content_youtube").select("*").in_("id", [response.data[0]["episode1_id"], response.data[0]["episode2_id"], response.data[0]["episode3_id"]]).execute()

    # Generate the script
    script = response.data[0]["intro"]+"\n\n"+summaries.data[0]["summary"]+"\n\n"+summaries.data[1]["summary"]+"\n\n"+summaries.data[2]["summary"]+"\n\n"+outro

    # Return the id, title and script
    return{"supabase_id":id, "title": response.data[0]["title"], "script": script}


# Function to generate the podcast and save to Supabase
def generate_podcast(id):
    print("generate podcast start")

    file_path = str(id) + ".mp3"
    mp3url = f"https://gvkfpctispwgsrwbpfgu.supabase.co/storage/v1/object/public/mydailydigest_episodes/{file_path}"

    # Check if the file already exists
    try:
        existing_file = supabase.storage.from_("mydailydigest_episodes").download(file_path)
        if existing_file.status_code == 200:
            print("File already exists. Returning existing MP3 URL.")
            return mp3url
    except Exception as e:
        # Handle case where file does not exist
        print(f"File does not exist: {e}")

    # Generate script
    script = generate_script(id)["script"]
    #script = "This hackathon rocks"

    # Generate audio from script
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    payload = {
        # "model_id": "eleven_multilingual_v2",
        "model_id": "eleven_turbo_v2",
        "text": script,
        "voice_settings": {
            "similarity_boost": 0.75,
            "stability": 0.63,
            "style": 0,
            "use_speaker_boost": True
        }
    }
    headers = {"Content-Type": "application/json","xi-api-key":os.environ.get("ELEVEN_API_KEY")}

    response = requests.request("POST", url, json=payload, headers=headers)

    # Save the content of the response to a file
    # file_path = uuid.uuid4().hex + ".mp3"
    with open(file_path, 'wb') as f:
        f.write(response.content)

    # Upload the file to Supabase storage
    with open(file_path, 'rb') as f:
        supabase.storage.from_("mydailydigest_episodes").upload(file=f, path=file_path, file_options={"content-type": "audio/mpeg"})

    supabase.table("podcast_episode").update({"mp3_url": mp3url, "script": script}).eq("id", id).execute()

    return mp3url

def get_podcasts():
    try:
        response = supabase.table("podcast_episode").select("*").execute()
        print(response)
        podcasts = response.data
        if response:
            return podcasts, 200
    except Exception as e:
        error(f"An exception occurred: {e}")
        return {"error": str(e)}, 500
    
def get_podcast_by_id(podcast_id):
    try:
        response = supabase.table("podcast_episode").select("*").eq('id', podcast_id).execute()
        podcast, error = response.data, response.error
        
        if error:
            error(f"Error fetching podcast by ID {podcast_id}: {error}")
            return None, error.message
        
        # Assuming the first item in the response data is the podcast
        return podcast[0] if podcast else None, None
    except Exception as e:
        error(f"An exception occurred: {e}")
        return None, str(e)



# Test function youtube_summary
#test = youtube_summary("https://www.youtube.com/watch?v=u5yGRLx5Tls")
#st.write(test["title"])

# Test the function podcast_intro
#test = podcast_intro("The Path to AGI", "The path to AGI is a long one, and we are only just beginning.", "Open AI Models", "Open AI models are the latest in AI research.", "Mixtral's Performance", "Mixtral's performance is impressive.",8,9,10)
#st.write(test["title"], test["intro"], test["supabase_id"])

# Test the function generate_script
#test = generate_script(2)
#st.title(test["title"])
#st.write(test["script"])

# Show available voices on elevenlabs
#url = "https://api.elevenlabs.io/v1/models"
#headers = {"xi-api-key":os.environ.get("ELEVEN_API_KEY")}
#response = requests.request("GET", url, headers=headers)
#st.write(response.json())

# Test the function generate_podcast
#mp3url = generate_podcast(2)
#st.audio(mp3url, format='audio/mp3')

# Show audio player
#mp3url = "https://gvkfpctispwgsrwbpfgu.supabase.co/storage/v1/object/public/mydailydigest_episodes/db390b6555e1474d95111cb7a40cb6c7.mp3"
#st.audio(mp3url, format='audio/mp3')

# Build the sidebar
with st.sidebar:
    
    # Input the Youtube video URLs
    url1 = st.text_input("Youtube URL 1", placeholder="Enter the URL of the YouTube video")
    url2 = st.text_input("Youtube URL 2", placeholder="Enter the URL of the YouTube video")
    url3 = st.text_input("Youtube URL 3", placeholder="Enter the URL of the YouTube video")

    # Submit button
    submit = st.button("Summarise")

    # If the submit button is clicked
    while submit:

        # Get the summaries
        summary1 = youtube_summary(url1)
        summary2 = youtube_summary(url2)
        summary3 = youtube_summary(url3)

        # Generate the intro
        intro = podcast_intro(summary1["title"], summary1["overview"], summary2["title"], summary2["overview"], summary3["title"], summary3["overview"], summary1["id"], summary2["id"], summary3["id"])

        # Generate the podcast
        mp3url = generate_podcast(intro["supabase_id"])

        # Show the podcast
        st.title(intro["title"])
        st.audio(mp3url, format='audio/mp3')

        # Reset the submit button
        submit = False