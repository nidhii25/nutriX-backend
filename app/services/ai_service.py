import os
import json
import google.generativeai as genai

# Load API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


# ---------------------------------------------------
# Utility: Diet Rules
# ---------------------------------------------------
DIET_RULES = {
    "veg": "- No meat, fish, chicken, seafood, or eggs.\n",
    "pure_veg": "- Strict vegetarian. No eggs, onion, garlic.\n",
    "nonveg": "- Non-veg allowed, balanced lean proteins.\n",
    "vegan": "- 100% plant-based. No dairy, eggs, honey.\n",
    "jain": "- Strict Jain. No root vegetables, onion, garlic.\n"
}


# ---------------------------------------------------
#  PLAN GENERATION (AI)
# ---------------------------------------------------
async def generate_plan_ai(user_profile, formData):
    # Extract dietary preference safely
    diet_type = user_profile.get("dietary_preferences", {}).get("diet_type", "veg")
    rules = DIET_RULES.get(diet_type, "")

    prompt = f"""
    Create a nutrition plan in VALID JSON ONLY.

    USER DIETARY PREFERENCE: {diet_type.upper()}

    STRICT RULES:
    {rules}
    - Never violate dietary preference.
    - All meals MUST comply.
    - If VEG or PURE_VEG → no eggs/meat/fish.
    - If JAIN → no onion, garlic, root vegetables.
    - If VEGAN → no dairy, eggs, honey.

    Required JSON format:
    {{
        "name": "string",
        "goal": "{formData.get("goal")}",
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

    SETTINGS:
    {json.dumps(formData)}

    Return ONLY JSON. No explanation.
    """

    response = model.generate_content(prompt)
    text = response.text.strip()

    start = text.find("{")
    end = text.rfind("}")

    json_text = text[start:end + 1]
    return json.loads(json_text)


# ---------------------------------------------------
#  SWAP MEAL (AI)
# ---------------------------------------------------
async def generate_swap_ai(meal):
    # Extract diet
    diet_type = meal.get("diet_type", "veg")
    rules = DIET_RULES.get(diet_type, "")

    prompt = f"""
    Replace this meal with a new one of similar macros.

    DIETARY PREFERENCE: {diet_type.upper()}

    STRICT RULES:
    {rules}
    - The replacement meal MUST follow the diet preference.

    ORIGINAL MEAL:
    {json.dumps(meal)}

    Return ONLY JSON:
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

    json_text = text[start:end + 1]
    return json.loads(json_text)
