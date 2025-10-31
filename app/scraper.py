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
    Returns formatted markdown text with summary at the top.
    """
    if not comments:
        return "## Pain Points Analysis\n\nNo comments available for analysis."

    # ✅ Combine all comment bodies into one text blob
    combined_text = "\n\n".join([f"- {c['body']}" for c in comments if c.get("body")])

    prompt = f"""
You are a market research AI analyzing Reddit comments to identify user pain points, frustrations, and unmet needs.

**TASK:**
Analyze these comments and extract the main PAIN POINTS users are expressing. 
Group similar complaints or frustrations together under thematic categories.

**RESPONSE FORMAT:**
Return your analysis in clear, well-structured markdown text with the following sections:

# User Pain Points Analysis

## 📊 Executive Summary
[Start with a concise 2-3 paragraph summary that gives an immediate overview of the main findings. Include:
- Overall sentiment and key frustrations
- Most common pain points
- Potential business opportunities
- Severity of issues mentioned]

## 🎯 Detailed Analysis

### Theme 1: [Theme Name]
- **Main Issues**: [Brief description]
- **User Quotes**: 
  - "[Direct quote illustrating pain point]"
  - "[Another relevant quote]"
- **Impact**: How this affects users
- **Frequency**: How commonly this issue appears

### Theme 2: [Theme Name]
- **Main Issues**: [Brief description]
- **User Quotes**: 
  - "[Direct quote illustrating pain point]"
  - "[Another relevant quote]"
- **Impact**: How this affects users
- **Frequency**: How commonly this issue appears

[Continue with additional themes as needed]

## 💡 Opportunity Insights
- Potential solutions or improvements suggested by users
- Unmet needs that could be addressed
- Common workarounds users are currently employing

## 🚨 Priority Recommendations
- Most urgent issues to address
- Quick wins that could improve user satisfaction
- Strategic opportunities for product development

**IMPORTANT:**
- Start with the Executive Summary at the very top after the main title
- Use proper markdown formatting with headers, bullet points, and emphasis
- Include direct user quotes to support your analysis
- Focus on specific, actionable pain points
- Keep the language clear and business-focused
- Do not use JSON format - return only markdown text

Here are the user comments to analyze:
{combined_text}
"""

    try:
        # ✅ Send to Groq model
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert market researcher specializing in extracting user pain points and frustrations from online discussions. You return well-formatted markdown analysis starting with a comprehensive executive summary, followed by detailed analysis with direct user quotes and actionable insights.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2000,
        )

        # ✅ Extract and return the markdown text directly
        analysis_text = response.choices[0].message.content.strip()
        return analysis_text

    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return f"# User Pain Points Analysis\n\n## 📊 Executive Summary\n\nAnalysis could not be completed due to an error: {str(e)}\n\nPlease try again with different comments."


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

        post_title = data[0]["data"]["children"][0]["data"].get(
            "title", "Untitled Post"
        )
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
                if body and body not in ["[deleted]", "[removed]"]:
                    result.append({"author": author, "body": body, "score": score})
            return result

        all_comments = extract_comments(comments_data)

        # ✅ Sort first
        if sort_by == "score":
            all_comments.sort(key=lambda x: x["score"], reverse=True)

        # ✅ Limit results
        limited_comments = all_comments[:limit]

        # ✅ Analyze pain points using Groq AI (now returns markdown text)
        pain_points_analysis = analyze_pain_points_with_groq(limited_comments)
        print("Analysis completed with summary at the top")

        return {
            "title": post_title,
            "comments": limited_comments,
            "pain_points_analysis": pain_points_analysis,  # Markdown text with summary first
            "comments_count": len(limited_comments),
        }

    except Exception as e:
        return {
            "error": f"Failed to fetch or process Reddit data: {str(e)}",
            "title": "Error",
            "comments": [],
            "pain_points_analysis": "# User Pain Points Analysis\n\n## 📊 Executive Summary\n\nUnable to fetch Reddit comments for analysis. Please check the URL and try again.",
            "comments_count": 0,
        }
