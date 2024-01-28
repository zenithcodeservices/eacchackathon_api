import substack_api
import requests
import re
from bs4 import BeautifulSoup

def extract_substack_author(url):
    try:
        # Regex pattern to match various Substack URL formats
        pattern = r'https?://(?:www\.)?([a-zA-Z0-9\-]+)\.substack\.com|https?://(?:www\.)?([a-zA-Z0-9\-]+)\.(?:com|co|io|net|org|edu|gov)'
        match = re.search(pattern, url)
        if match:
            # Extract the relevant group based on the URL format
            return match.group(1) or match.group(2)
        else:
            raise ValueError("No valid Substack author or custom domain found in the URL.")
    except Exception as e:
        return f"An error occurred: {e}"

# Test the function with different URLs
urls = [
    'https://dpereira.substack.com/p/product-owner-beyond-scrum-cbd?utm_source=%2Finbox&utm_medium=reader2',
    'https://www.notboring.co/p/weekly-dose-of-optimism-78?utm_source=%2Finbox&utm_medium=reader2',
    'https://www.weekendbriefing.com/p/weekend-briefing-no-520?utm_source=%2Finbox&utm_medium=reader2',
    'https://notboring.substack.com/p/weekly'
]


def get_substack_posts(name):
    posts = substack_api.get_newsletter_post_metadata(name, start_offset=0, end_offset=3)  # Get top 3 articles
    articles = []  # Initialize the list to store articles

    for post in posts:
        # Get the post contents using the slug
        post_content = substack_api.get_post_contents(name, post.get('slug'))

        html = post_content['body_html']

        # Use Beautiful Soup to parse the HTML content
        soup = BeautifulSoup(html, 'html.parser')

        # Extract text from all paragraph <p> tags
        article_text = []  # Initialize the list to store paragraphs
        for paragraph in soup.find_all('p'):
            article_text.append(paragraph.get_text(strip=True))

        # Join all paragraphs into a single string, separated by a newline
        full_article = "\n".join(article_text)

        # Create a dictionary with the title and the article content
        article_dict = {
            'title': post_content['title'],
            'article': full_article,
            'created_at': post_content['post_date'],
            'url': post_content['canonical_url']
        }

        # Append the dictionary to the list of articles
        articles.append(article_dict)
        
    return articles