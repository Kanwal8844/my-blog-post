import time
import requests
import pickle
import os
from groq import Groq
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# API Keys
GROQ_API_KEY = "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"
UNSPLASH_KEY = "UE70h0Bf4EpxJYc58s2sckl6mBVoPx9x0JkDDF5duEg"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.pickle')
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, 'credentials.json')

client = Groq(api_key=GROQ_API_KEY)

PROMPT_TEMPLATE = """
You are an expert blogger. Write a complete, original blog article about: {topic}.
STRICT FORMATTING RULES:
1. WRITE IN VALID HTML FORMAT.
2. Use <h2> for main headings and <h3> for sub-headings.
3. Wrap every paragraph in <p> tags.
4. AFFILIATE LINK: Insert this link: <p>Recommended Resource: <a href="https://radiantagelessbeautysecrets.com/#aff=Hashmi8844" target="_blank">Click here for your radiant skin guide</a></p>
5. NO dash characters.
6. Return Title on the first line, then HTML-formatted article.
"""

blogs = [
    {"name": "GlowRoutineDaily", "id": "364166265250095354", "count": 0},
    {"name": "NaturalSkinVibes", "id": "7090707736809202292", "count": 0},
    {"name": "PureSkinSecrets", "id": "4397670016656351793", "count": 0},
    {"name": "BeautyFixRoutine", "id": "1052239470635177525", "count": 0},
    {"name": "RadiantFaceTips", "id": "340863184931384661", "count": 0}
]

def get_blogger_service():
    creds = None
    # 1. Check if token file exists
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
            
    # 2. If no valid credentials, run flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=['https://www.googleapis.com/auth/blogger']
            )
            # PC par browser khulne ke liye
            creds = flow.run_local_server(port=8080)
            
            # Save the file
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
                
    return build('blogger', 'v3', credentials=creds)

def get_post_content(blog_name):
    topic_chat = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Give one specific, fresh trending skincare topic for {blog_name}."}],
        model="llama-3.3-70b-versatile",
    )
    topic = topic_chat.choices[0].message.content
    article_chat = client.chat.completions.create(
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
        model="llama-3.3-70b-versatile",
    )
    article_full = article_chat.choices[0].message.content
    lines = article_full.split('\n', 1)
    title = lines[0] if len(lines) > 0 else "Untitled"
    content = lines[1] if len(lines) > 1 else "Content missing"
    img_url = requests.get(f"https://api.unsplash.com/photos/random?query=skincare&client_id={UNSPLASH_KEY}").json()['urls']['regular']
    return title, content, img_url

def post_to_blogger(blog_id, title, content, img_url):
    service = get_blogger_service()
    post_body = {'kind': 'blogger#post', 'title': title, 'content': f'<img src="{img_url}"/><br/><br/>{content}'}
    service.posts().insert(blogId=blog_id, body=post_body).execute()
    print(f"Successfully posted: {title}")

# مین لوپ
while True:
    for blog in blogs:
        if blog["count"] < 5:
            try:
                print(f"Posting to: {blog['name']} ({blog['count']+1}/5)")
                title, content, img = get_post_content(blog['name'])
                post_to_blogger(blog['id'], title, content, img)
                blog["count"] += 1
                time.sleep(3600)
            except Exception as e:
                print(f"Error on {blog['name']}: {e}")
                time.sleep(300)
        
    if all(blog["count"] >= 5 for blog in blogs):
        print("Daily limit reached. Waiting for next cycle...")
        for blog in blogs: blog["count"] = 0
        time.sleep(3600)