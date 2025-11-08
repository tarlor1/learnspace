import os
import httpx
import json
from typing import List, Dict, Any
from models import Question
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# NeuralSeek API Configuration
NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL", "https://api.neuralseek.com/v1")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY", "your-api-key-here")
NEURALSEEK_EMBED_CODE = os.getenv("NEURALSEEK_EMBED_CODE", "your-embed-code-here")

# NeuralSeek Agent Names - customize these based on your actual agent names
QUESTION_GENERATOR_AGENT = os.getenv("QUESTION_GENERATOR_AGENT", "question_generator_agent")
ANSWER_VALIDATOR_AGENT = os.getenv("ANSWER_VALIDATOR_AGENT", "answer_validator_agent")
CONTENT_ANALYZER_AGENT = os.getenv("CONTENT_ANALYZER_AGENT", "content_analyzer_agent")

print(f"✅ Loaded NeuralSeek Config:")
print(f"   URL: {NEURALSEEK_API_URL}")
print(f"   API Key: {'*' * 20}{NEURALSEEK_API_KEY[-4:] if len(NEURALSEEK_API_KEY) > 4 else '****'}")
print(f"   EMBED CODE: {'*' * 20}{NEURALSEEK_EMBED_CODE[-4:] if len(NEURALSEEK_EMBED_CODE) > 4 else '****'}")
print(f"   Question Agent: {QUESTION_GENERATOR_AGENT}")

async def generate_questions_with_neuralseek(num_questions: int = 10) -> List[Question]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "embedcode": NEURALSEEK_EMBED_CODE
    }

    print(f"\n🤖 Generating {num_questions} questions via NeuralSeek")
    print(f"📡 API URL: {NEURALSEEK_API_URL}/maistro")
    
    questions = []
    
    # Make multiple requests to generate questions one at a time
    async with httpx.AsyncClient(timeout=60) as client:
        for i in range(num_questions):
            try:
                payload = {"agent": QUESTION_GENERATOR_AGENT}
                
                response = await client.post(
                    f"{NEURALSEEK_API_URL}/maistro", 
                    json=payload, 
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"✅ Response {i+1}: {response.status_code}")
                print(f"📦 Data: {json.dumps(result, indent=2)[:300]}...")

            except Exception as e:
                import traceback
                traceback.print_exc()
    
    print(f"\n✅ Total questions generated: {len(questions)}")
    return questions[:num_questions]  # Ensure we return exactly num_questions

async def validate_answer_with_neuralseek(question_text: str, user_answer: str) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "embedcode": NEURALSEEK_EMBED_CODE
    }

    print(f"\n🤖 Validating Answer via NeuralSeek")
    print(f"📡 API URL: {NEURALSEEK_API_URL}/maistro")
    
    try:
        parameters = {
            "question": question_text,
            "answer": user_answer
        }
        
        print(f"🤖 Calling NeuralSeek agent: {ANSWER_VALIDATOR_AGENT}")

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                payload = {"agent": ANSWER_VALIDATOR_AGENT}
                
                response = await client.post(
                    f"{NEURALSEEK_API_URL}/maistro", 
                    json=payload, 
                    headers=headers,
                    parameters=parameters
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"📦 Data: {json.dumps(result, indent=2)[:300]}...")

            except Exception as e:
                import traceback
                traceback.print_exc()

        return None
        
    except Exception as e:
        # Return default validation result if API fails
        return {
            "score": 0.5,
            "feedback": "Unable to automatically grade this answer. Manual review recommended.",
            "is_correct": None,
            "suggestions": []
        }