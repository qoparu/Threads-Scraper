import re, json, requests
from dotenv import load_dotenv
import os
load_dotenv()

cookie = os.getenv("THREADS_COOKIE", "")

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Cookie": cookie,
})

with open("response_tag.html", encoding="utf-8") as f:
    html = f.read()

# Find all JS file references
js_srcs = re.findall(r'"(https://static\.cdninstagram\.com/rsrc\.php/[^"]+\.js[^"]*)"', html)
js_srcs = list(dict.fromkeys(js_srcs))  # deduplicate
print(f"Found {len(js_srcs)} unique JS files")

# Keywords to search in JS files
keywords = [
    "tag_name", "hashtag", "TagFeed", "HashtagFeed", "BarcelonaTag",
    "TaggedContent", "tag_feed", "barcelona_hashtag",
]

found_doc_ids = {}

for src in js_srcs:
    try:
        r = s.get(src, timeout=15)
        js = r.text
        fname = src.split("/")[-1][:30]

        for kw in keywords:
            if kw.lower() in js.lower():
                # Find doc_ids near this keyword
                pattern = re.compile(
                    rf'.{{0,300}}{re.escape(kw)}.{{0,300}}"(\d{{15,}})"',
                    re.IGNORECASE | re.DOTALL
                )
                matches = pattern.findall(js)
                if matches:
                    print(f"  [{fname}] keyword='{kw}' -> doc_ids: {matches[:3]}")
                    for m in matches[:3]:
                        found_doc_ids[m] = kw

    except Exception as e:
        print(f"  Error fetching {src[-40:]}: {e}")

print()
print("All found doc_ids:", list(found_doc_ids.keys()))

# Test found doc_ids with GraphQL
if found_doc_ids:
    print()
    print("=== Testing found doc_ids ===")

    with open("response_tag.html", encoding="utf-8") as f:
        html2 = f.read()
    m = re.search(r'"token":"([A-Za-z0-9_\-]{20,})".*?"async_get_token"', html2)
    lsd = m.group(1) if m else ""

    gql = requests.Session()
    gql.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        "Cookie": cookie,
        "x-ig-app-id": "238260118697367",
        "x-fb-lsd": lsd,
        "origin": "https://www.threads.net",
        "referer": "https://www.threads.net/tag/almaty",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
    })

    for doc_id in list(found_doc_ids.keys())[:10]:
        for variables in [
            {"tag_name": "almaty", "first": 3},
            {"tag_name": "almaty"},
            {"query": "almaty", "first": 3},
        ]:
            payload = {
                "variables": json.dumps(variables),
                "doc_id": doc_id,
                "lsd": lsd,
            }
            r2 = gql.post(
                "https://www.threads.net/api/graphql",
                data=payload,
                headers={"content-type": "application/x-www-form-urlencoded"},
                timeout=12,
            )
            ct = r2.headers.get("Content-Type","")
            if "json" in ct:
                try:
                    d = r2.json()
                    data_d = d.get("data") or {}
                    errors = d.get("errors") or []
                    if data_d and not errors:
                        print(f"  doc_id={doc_id} vars={list(variables.keys())} -> SUCCESS data_keys={list(data_d.keys())}")
                    elif errors:
                        print(f"  doc_id={doc_id}: errors={[e.get('message','?')[:50] for e in errors[:2]]}")
                except:
                    pass
