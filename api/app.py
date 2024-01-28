from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
import supabase
from flask_cors import CORS
from podcast_generator import youtube_summary, podcast_intro, generate_podcast, get_podcasts, get_podcast_by_id
from supabase import create_client, Client

from dotenv import load_dotenv
env_path = '../../.env.local'
# import your OpenAI key
# Load the environment variables from the specified .env file
load_dotenv(dotenv_path=env_path)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/podcasts": {"origins": "*"}})  # Adjust the origins as needed

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
print("Supabase URL: ", supabase_url)
print("Supabase Key: ", supabase_key)
supabase = create_client(supabase_url, supabase_key)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.route('/generate-podcast', methods=['POST'])
def generate_podcast_endpoint():
    data = request.json
    creators = data['creators']

    # Assuming creators array contains YouTube URLs
    summaries = [youtube_summary(url) for url in creators if url]
    print("Summaries: ", summaries)

    # Extract relevant details for podcast intro
    intro_details = [(summary["id"], summary["summary"], summary["title"], summary["overview"]) for summary in summaries]

    # Initialize default values for missing summaries
    default_summary = {"id": 0, "summary": "", "overview": "", "title": ""}

    # Ensure we have exactly three summaries
    while len(summaries) < 3:
        summaries.append(default_summary)

    # Prepare arguments for podcast_intro
    intro_args = []
    for summary in summaries:
        intro_args.extend([summary["title"], summary["overview"]])

    print("Intro args pre ID: ", intro_args)

    intro_args.extend([int(summary["id"]) for summary in summaries])

    print("Intro args: ", intro_args)

    # Generate podcast intro and MP3 URL
    intro = podcast_intro(*intro_args)
    print("Intro: ", intro)

    mp3url = generate_podcast(intro["supabase_id"])

    return jsonify({"mp3url": mp3url}), 200

@app.route('/podcasts', methods=['GET'])
def get_podcast_list():
    podcasts, status = get_podcasts()
    return jsonify(podcasts), status

@app.route('/podcast/<int:podcast_id>', methods=['GET'])
def get_podcast(podcast_id):
    podcast, error_message = get_podcast_by_id(podcast_id)
    if podcast:
        return jsonify(podcast), 200
    else:
        return jsonify({"error": error_message}), 500 if error_message else 404


if __name__ == "__main__":
    app.run(port=5001, debug=True)
