# Import libraries
import os
from supabase import create_client, Client
import requests
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


# Function to generate an RSS feed
def generate_rss(id):

    # Get the podcast episode from Supabase
    response = supabase.table("podcast_episode").select("*").eq("id", id).execute()

    # Create the RSS feed
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"
    xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>My Daily Digest</title>
    <link>https://mydailydigest.show</link>
    <description>My Daily Digest brings you a summary of the latest content from your favourite YouTube channels.</description>
    <itunes:owner>
        <itunes:email>you@mydailydigest.tech</itunes:email>
    </itunes:owner>
    <itunes:author>My Daily Digest</itunes:author><itunes:image href="https://gvkfpctispwgsrwbpfgu.supabase.co/storage/v1/object/public/mydailydigest_episodes/mydailydigest.png"/>
    <language>en-us</language>
    <lastBuildDate>{response.data[0]["created_at"]}</lastBuildDate>
    <pubDate>{response.data[0]["created_at"]}</pubDate>
    <ttl>1800</ttl>
    <image>
        <url>https://gvkfpctispwgsrwbpfgu.supabase.co/storage/v1/object/public/mydailydigest_episodes/mydailydigest.png</url>
        <title>My Daily Digest</title>
        <link>https://mydailydigest.show</link>
    </image>
    <item>
        <title>{response.data[0]["title"]}</title>
        <description>{response.data[0]["intro"]}</description>
        <pubDate>{response.data[0]["created_at"]}</pubDate>
        <enclosure url="{response.data[0]["mp3_url"]}" length="0" type="audio/mpeg"/>
        <guid>{response.data[0]["mp3_url"]}</guid>
    </item>
    </channel>
    </rss>
    """

    # Return the RSS feed
    return rss

# Create a function to generate a QR code
def generate_qr(url):
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+url
    return qr_url