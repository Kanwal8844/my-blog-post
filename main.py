import time
import requests
import json
import pickle
import os
import random
from groq import Groq
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# API Keys
GROQ_API_KEY = "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"
PINTEREST_BOARD_ID = "945122671824200517"
CSRF_TOKEN = "2f34ed73d33f780285ba8dffed4b5526"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.pickle')
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, 'credentials.json')
LINKS_FILE = os.path.join(BASE_DIR, 'links.txt')

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

def get_random_image_link():
    with open(LINKS_FILE, 'r') as f:
        links = [line.strip() for line in f if line.strip()]
    return random.choice(links)

def post_to_pinterest(image_url, title, description):
    try:
        with open('pinterest_cookies.json', 'r') as f:
            cookies_list = json.load(f)
        session = requests.Session()
        for cookie in cookies_list:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        
        url = "https://www.pinterest.com/resource/PinCreateResource/create/"
        
        # Ye rahe updated headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "X-CSRFToken": CSRF_TOKEN,
            "X-Requested-With": "XMLHttpRequest",
            "X-App-Type": "compiled",
            "Referer": "https://www.pinterest.com/",
            "Origin": "https://www.pinterest.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "source_url": "/pin-builder/",
            "data": json.dumps({
                "options": {
                    "board_id": PINTEREST_BOARD_ID,
                    "description": description,
                    "link": "https://radiantagelessbeautysecrets.com/#aff=Hashmi8844",
                    "title": title,
                    "image_url": image_url,
                    "method": "pin_create"
                },
                "context": {}
            })
        }
        
        response = session.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            print(f"Pinterest Post Successful: {title}")
        else:
            print(f"Pinterest Failed! Status: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Pinterest Error: {e}")

def get_blogger_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=['https://www.googleapis.com/auth/blogger'])
            creds = flow.run_local_server(port=8080)
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
    return build('blogger', 'v3', credentials=creds)

def get_post_content(blog_name):
    topic_chat = client.chat.completions.create(messages=[{"role": "user", "content": f"Give one specific, fresh trending skincare topic for {blog_name}."}], model="llama-3.3-70b-versatile")
    topic = topic_chat.choices[0].message.content
    article_chat = client.chat.completions.create(messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}], model="llama-3.3-70b-versatile")
    article_full = article_chat.choices[0].message.content
    lines = article_full.split('\n', 1)
    title = lines[0] if len(lines) > 0 else "Untitled"
    content = lines[1] if len(lines) > 1 else "Content missing"
    img_url = get_random_image_link()
    return title, content, img_url

def post_to_blogger(blog_id, title, content, img_url):
    service = get_blogger_service()
    post_body = {'kind': 'blogger#post', 'title': title, 'content': f'<img src="{img_url}"/><br/><br/>{content}'}
    service.posts().insert(blogId=blog_id, body=post_body).execute()
    print(f"Successfully posted to Blogger: {title}")

while True:
    for blog in blogs:
        if blog["count"] < 5:
            try:
                print(f"Posting to: {blog['name']} ({blog['count']+1}/5)")
                title, content, img = get_post_content(blog['name'])
                post_to_blogger(blog['id'], title, content, img)
                post_to_pinterest(img, title, title)
                blog["count"] += 1
                time.sleep(3600)
            except Exception as e:
                print(f"Error on {blog['name']}: {e}")
                time.sleep(300)
        
    if all(blog["count"] >= 5 for blog in blogs):
        print("Daily limit reached.")
        for blog in blogs: blog["count"] = 0
        time.sleep(3600)
