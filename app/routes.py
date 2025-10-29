from fastapi import APIRouter, HTTPException, Request, Response
from app.scraper import fetch_reddit_comments
import time

router = APIRouter()

# 🧠 Rate limit setup
request_log = []
MAX_REQUESTS = 2
WINDOW_SECONDS = 60  # 1 minute


def allow_request():
    current_time = time.time()
    while request_log and current_time - request_log[0] > WINDOW_SECONDS:
        request_log.pop(0)
    if len(request_log) >= MAX_REQUESTS:
        return False
    request_log.append(current_time)
    return True


@router.post("/fetch_data")
async def fetch_data(request: Request):
    if not allow_request():
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again after 1 minute.")

    data = await request.json()
    url = data.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="Missing URL field")

    if "reddit" not in url.lower():
        raise HTTPException(status_code=400, detail="Please provide a valid Reddit URL")

    print("✅ Got request from frontend")

    # Fetch Reddit data + AI analysis
    result = await fetch_reddit_comments(url)

    # Extract title + pain points
    title = result.get("title", "Untitled Post")
    pain_points = result.get("pain_points", {})
    themes = pain_points.get("themes", [])
    summary = pain_points.get("summary", "No summary found.")

    # 🧱 Build readable plain text
    text_output = f"📰 Post Title:\n{title}\n\n"

    for theme in themes:
        topic = theme.get("topic", "Untitled Theme")
        points = theme.get("pain_points", [])
        text_output += f"🔹 {topic}:\n"
        for p in points:
            text_output += f"   • {p}\n"
        text_output += "\n"

    text_output += f"🧠 Summary:\n{summary}\n"

    return Response(content=text_output, media_type="text/plain")


@router.get("/test")
async def test_endpoint():
    return {"message": "API is working", "status": "success"}
