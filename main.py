import time
import requests
import pickle
import os
import json
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
COOKIES_PATH = os.path.join(BASE_DIR, 'pinterest_cookies.json')

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
    try:
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
    except Exception as e:
        print(f"CRITICAL ERROR: Blogger Service Connection Failed: {e}")
        return None

def post_to_pinterest(image_url, title, description):
    print(f"DEBUG: Attempting to pin to Pinterest: {title}")
    try:
        if not os.path.exists(COOKIES_PATH):
            print("Pinterest Error: cookies file not found!")
            return
        
        with open(COOKIES_PATH, 'r') as f:
            cookies_list = json.load(f)
        session = requests.Session()
        for cookie in cookies_list:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        
        url = "https://www.pinterest.com/resource/PinCreateResource/create/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-CSRFToken": "YOUR_CSRF_TOKEN_HERE", # Yahan apna Token daalein
            "X-Requested-With": "XMLHttpRequest"
        }
        data = {
            "data": json.dumps({"options": {"board_id": "945122671824200517", "description": description, "link": "https://radiantagelessbeautysecrets.com/#aff=Hashmi8844", "title": title, "image_url": image_url, "method": "pin_create"}})
        }
        response = session.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            print(f"SUCCESS: Pinterest Post Successful: {title}")
        else:
            print(f"Pinterest Error: Failed with status code {response.status_code}. Response: {response.text}")
    except Exception as e:
        print(f"Pinterest Exception: {e}")

def get_post_content(blog_name):
    try:
        topic_chat = client.chat.completions.create(messages=[{"role": "user", "content": f"Give one specific, fresh trending skincare topic for {blog_name}."}], model="llama-3.3-70b-versatile")
        topic = topic_chat.choices[0].message.content
        article_chat = client.chat.completions.create(messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}], model="llama-3.3-70b-versatile")
        article_full = article_chat.choices[0].message.content
        lines = article_full.split('\n', 1)
        title = lines[0] if len(lines) > 0 else "Untitled"
        content = lines[1] if len(lines) > 1 else "Content missing"
        img_url = requests.get(f"https://api.unsplash.com/photos/random?query=skincare&client_id={UNSPLASH_KEY}").json()['urls']['regular']
        return title, content, img_url
    except Exception as e:
        print(f"Error in Content Generation: {e}")
        return None, None, None

def post_to_blogger(blog_id, title, content, img_url):
    try:
        service = get_blogger_service()
        if service:
            post_body = {'kind': 'blogger#post', 'title': title, 'content': f'<img src="{img_url}"/><br/><br/>{content}'}
            service.posts().insert(blogId=blog_id, body=post_body).execute()
            print(f"SUCCESS: Successfully posted to Blogger: {title}")
        else:
            print("Blogger post skipped due to service error.")
    except Exception as e:
        print(f"Blogger Post Error: {e}")

while True:
    for blog in blogs:
        if blog["count"] < 5:
            title, content, img = get_post_content(blog['name'])
            if title and content and img:
                post_to_blogger(blog['id'], title, content, img)
                post_to_pinterest(img, title, title)
                blog["count"] += 1
            else:
                print(f"Skipping {blog['name']} due to content error.")
            time.sleep(3600)
        
    if all(blog["count"] >= 5 for blog in blogs):
        print("Daily limit reached. Resetting count.")
        for blog in blogs: blog["count"] = 0
        time.sleep(3600)
