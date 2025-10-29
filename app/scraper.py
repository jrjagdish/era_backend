# scraper.py
import aiohttp
import asyncio
import os
import json
from groq import Groq
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ------------------------ GROQ AI ANALYSIS ------------------------
def analyze_pain_points_with_groq(comments):
    """
    Send Reddit comments to Groq AI and extract user pain points.
    Returns proper Python dictionary instead of JSON string.
    """
    if not comments:
        return {"themes": [], "summary": "No comments available for analysis."}
    

        # ✅ Combine all comment bodies into one text blob
    combined_text = "\n\n".join(
        [f"- {c['body']}" for c in comments if c.get("body")]
    )

    prompt = f"""
You are a market research AI. The following are Reddit user comments discussing their problems, frustrations, or experiences.

Analyze these comments and identify the main PAIN POINTS users are expressing. 
Group similar complaints or frustrations together under a theme.

Return your answer in a structured JSON format:
{{
    "themes": [
        {{
            "topic": "<short descriptive label>",
            "pain_points": ["...", "..."]
        }}
    ],
    "summary": "<short overall insight>"
}}

IMPORTANT: Return ONLY valid JSON, no additional text, no markdown code blocks, no explanations.

Here are the user comments:
{combined_text}
"""

    try:
        # ✅ Send to Groq model
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",  # You can also use "llama3-8b-8192" or "gemma-7b-it"
            messages=[
                {"role": "system", "content": "You are an expert in startup idea validation and user pain point extraction. Always return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"}  # Force JSON response
        )

        # ✅ Extract the JSON from response
        response_text = response.choices[0].message.content
        
        # ✅ Clean the response - remove markdown code blocks if present
        cleaned_response = response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # Remove ```json
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]  # Remove ```
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # Remove ```
        
        # ✅ Parse JSON to Python dictionary
        pain_points_data = json.loads(cleaned_response)
        return pain_points_data

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text}")
        return {"error": "Failed to parse AI response", "raw_response": response_text}
    
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {"error": f"AI analysis failed: {str(e)}"}


# ------------------------ REDDIT SCRAPER ------------------------
async def fetch_reddit_comments(url: str, limit: int = 30, sort_by: str = "score"):
    """Fetch Reddit comments, optionally sort, limit, and analyze pain points."""
    if not url.endswith(".json"):
        if not url.endswith("/"):
            url += "/"
        url += ".json"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        post_title = data[0]["data"]["children"][0]["data"].get("title", "Untitled Post")
        comments_data = data[1]["data"]["children"]

        def extract_comments(comments):
            result = []
            for c in comments:
                if c["kind"] != "t1":
                    continue
                d = c["data"]
                body = d.get("body")
                author = d.get("author")
                score = d.get("score", 0)
                if body and body not in ['[deleted]', '[removed]']:
                    result.append({"author": author, "body": body, "score": score})
            return result

        all_comments = extract_comments(comments_data)

        # ✅ Sort first
        if sort_by == "score":
            all_comments.sort(key=lambda x: x["score"], reverse=True)
        # elif sort_by == "new":
        #     all_comments.sort(key=lambda x: x.get("created_utc", 0), reverse=True)

        # ✅ Limit results
        limited_comments = all_comments[:limit]

        # ✅ Analyze pain points using Groq AI
        pain_points = analyze_pain_points_with_groq(limited_comments)
        print("details sent")

        return {
            "title": post_title,
            "comments": limited_comments,
            "pain_points": pain_points,  # Now this is a proper dict, not string
        }

    except Exception as e:
        return {
            "error": f"Failed to fetch or process Reddit data: {str(e)}",
            "title": "Error",
            "comments": [],
            "pain_points": {"themes": [], "summary": "Analysis failed due to scraping error"}
        }