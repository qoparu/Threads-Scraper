import os, json, re, requests
from urllib.parse import quote
from dotenv import load_dotenv
load_dotenv()

cookie = os.getenv("THREADS_COOKIE", "")
csrftoken = os.getenv("THREADS_CSRFTOKEN", "")
USER_ID = "29190522985"

# ── Get LSD token from Threads main page ────────────────────────────────────
web = requests.Session()
web.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Cookie": cookie,
})
html = web.get("https://www.threads.net/", timeout=15).text
m = re.search(r'"token":"([A-Za-z0-9_\-]{20,})".*?"async_get_token"', html)
lsd_token = m.group(1) if m else ""
print("LSD/fb_dtsg token:", lsd_token)

# Also try to find doc_ids from JS files
print()
print("=== Scan JS for Threads doc_ids ===")
script_srcs = re.findall(r'src="(https://static\.cdn[^"]+\.js[^"]*)"', html)
print(f"Found {len(script_srcs)} JS files")
hashtag_doc_ids = []
for src in script_srcs[:5]:  # check first 5 JS files
    try:
        js = web.get(src, timeout=10).text
        # Look for doc_id near hashtag/tag references
        matches = re.findall(r'(?:Hashtag|hashtag|TagFeed|tagFeed).{0,200}?"(\d{15,})"', js)
        if matches:
            print(f"  {src.split('/')[-1][:30]}: doc_ids near hashtag = {matches[:3]}")
            hashtag_doc_ids.extend(matches)
    except:
        pass

print()
print("=== Full sections response (mobile UA) ===")
s = requests.Session()
s.headers.update({
    "User-Agent": "Barcelona 289.0.0.77.109 Android",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "x-ig-app-id": "238260118697367",
    "X-CSRFToken": csrftoken,
    "ig-u-ds-uid": USER_ID,
    "ig-intended-user-id": USER_ID,
    "Cookie": cookie,
})
r = s.post(
    "https://www.threads.net/api/v1/tags/almaty/sections/",
    data={"tab_type": "recent", "include_persistent": "1"},
    timeout=15,
)
d = r.json()
print(json.dumps(d, ensure_ascii=False, indent=2)[:3000])

print()
print("=== GraphQL with lsd token ===")
gql = requests.Session()
gql.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Cookie": cookie,
    "x-ig-app-id": "238260118697367",
    "X-CSRFToken": csrftoken,
    "x-fb-lsd": lsd_token,
    "x-fb-friendly-name": "BarcelonaHashtagFeedQuery",
    "origin": "https://www.threads.net",
    "referer": "https://www.threads.net/tag/almaty",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "content-type": "application/x-www-form-urlencoded",
})

# Try with lsd token for various doc_ids
for doc_id in ["6940876296036459", "7357711674327297", "7051000028290507", "25531498203362078"]:
    for vars_dict in [
        {"tag_name": "almaty", "first": 3},
        {"query": "алматы", "first": 3},
    ]:
        payload = {
            "variables": json.dumps(vars_dict),
            "doc_id": doc_id,
            "lsd": lsd_token,
        }
        r2 = gql.post("https://www.threads.net/api/graphql", data=payload, timeout=15)
        ct = r2.headers.get("Content-Type","")[:30]
        if "json" in ct:
            try:
                d2 = r2.json()
                data2 = d2.get("data") or {}
                errors = d2.get("errors") or []
                print(f"doc_id={doc_id} vars={list(vars_dict.keys())} -> data_keys={list(data2.keys())[:4]} errors={len(errors)}")
                if data2:
                    for k, v in data2.items():
                        if isinstance(v, dict):
                            edges = v.get("edges",[])
                            if edges:
                                print(f"  *** FOUND edges in {k}: {len(edges)} items!")
                                print(f"  First edge: {json.dumps(edges[0], ensure_ascii=False)[:300]}")
            except Exception as e:
                print(f"  JSON error: {e}, body: {r2.text[:100]}")
        else:
            if r2.status_code != 200:
                print(f"doc_id={doc_id}: {r2.status_code}")
