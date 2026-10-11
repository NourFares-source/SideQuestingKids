# app/services/ai_verifier.py
import os
from typing import List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types

# Pydantic schema to enforce structured JSON output from Gemini
class AIVerificationResult(BaseModel):
    passed: bool
    feedback: str

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def verify_quest_submission(
    current_image_path: str,
    quest_title: str,
    quest_description: str,
    system_prompt: Optional[str],
    previous_submissions: List[dict] = None
) -> AIVerificationResult:
    """
    Sends the current submission image and historical context to Gemini Vision for evaluation.
    """
    if previous_submissions is None:
        previous_submissions = []

    # 1. Base Prompt Assembly
    instructions = (
        f"You are an AI Quest Inspector for a game app.\n"
        f"Quest Title: {quest_title}\n"
        f"Quest Description: {quest_description}\n"
    )
    if system_prompt:
        instructions += f"Verification Criteria / Prompt: {system_prompt}\n"

    instructions += (
        "\nEvaluate if the user's latest image fulfills the quest requirements. "
        "Be encouraging, objective, and clear in your feedback."
    )

    contents = [instructions]

    # 2. Append Historical Context for Multi-Day Continuity
    for sub in previous_submissions:
        step = sub.get("step_number")
        feedback = sub.get("feedback")
        img_path = sub.get("image_path")
        
        contents.append(f"--- Historical Submission for Step {step} ---")
        contents.append(f"Previous AI Feedback: {feedback}")
        
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as f:
                image_bytes = f.read()
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                )
            )

    # 3. Append Current Submission Image
    contents.append("--- Current Image Submission ---")
    with open(current_image_path, "rb") as f:
        curr_image_bytes = f.read()
        
    contents.append(
        types.Part.from_bytes(
            data=curr_image_bytes,
            mime_type="image/jpeg"
        )
    )

    # 4. Request Gemini structured JSON response
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIVerificationResult,
            temperature=0.2,
        ),
    )

    # Return validated Pydantic object
    return AIVerificationResult.model_validate_json(response.text)