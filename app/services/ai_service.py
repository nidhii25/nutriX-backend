import os
import json
import google.generativeai as genai

# Works even if Pylance shows error
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")  # or "gemini-1.5", "gemini-1.5-pro", etc.


async def generate_plan_ai(user_profile, formData):
    prompt = f"""
    Create a nutrition plan in VALID JSON. 
    Return ONLY JSON.

    Required Format:
    {{
        "name": "string",
        "goal": "string",
        "duration": {formData["duration"]},
        "days": [
            {{
                "day": 1,
                "tag": "Training",
                "meals": [
                    {{
                        "id": "uuid",
                        "time": "08:00 AM",
                        "name": "Oatmeal",
                        "description": "string",
                        "calories": 350,
                        "protein": 25,
                        "carbs": 40,
                        "fats": 10,
                        "status": "pending"
                    }}
                ]
            }}
        ]
    }}

    USER PROFILE:
    {json.dumps(user_profile)}

    PLAN SETTINGS:
    {json.dumps(formData)}

    Return ONLY JSON, no markdown, no explanation.
    """

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Extract JSON safely
    start = text.find("{")
    end = text.rfind("}")

    json_text = text[start:end+1]
    return json.loads(json_text)



async def generate_swap_ai(meal):
    prompt = f"""
    Replace this meal with another one of similar macros.

    Original Meal:
    {json.dumps(meal)}

    Return only JSON:
    {{
        "id": "uuid",
        "time": "string",
        "name": "string",
        "description": "string",
        "calories": number,
        "protein": number,
        "carbs": number,
        "fats": number,
        "status": "pending",
        "isSwapped": true
    }}
    """

    response = model.generate_content(prompt)
    text = response.text.strip()

    start = text.find("{")
    end = text.rfind("}")

    json_text = text[start:end+1]
    return json.loads(json_text)
