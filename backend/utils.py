import os
import httpx
import asyncio
from typing import List, Dict, Any
from models import Question
from dotenv import load_dotenv

load_dotenv()

NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL", "https://api.neuralseek.com/v1")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY")
NEURALSEEK_EMBED_CODE = os.getenv("NEURALSEEK_EMBED_CODE")
QUESTION_GENERATOR_AGENT = os.getenv("QUESTION_GENERATOR_AGENT", "question_generator_agent")
ANSWER_VALIDATOR_AGENT = os.getenv("ANSWER_VALIDATOR_AGENT", "answer_validator_agent")

if not all([NEURALSEEK_API_KEY, NEURALSEEK_EMBED_CODE, QUESTION_GENERATOR_AGENT, ANSWER_VALIDATOR_AGENT]):
    raise ValueError("One or more NeuralSeek environment variables are not set. Please check your .env file.")

async def _fetch_one_question(client: httpx.AsyncClient, headers: Dict[str, str], topic: str) -> Question:
    """Call NeuralSeek once and map the response to our Question model."""
    payload = {"agent": QUESTION_GENERATOR_AGENT, "params": [{"name": "chosenTopic", "value": topic}], "options": {"temperatureMod": 20, "maxTokens": 25}}
    response = await client.post(f"{NEURALSEEK_API_URL}/maistro", json=payload, headers=headers)
    print(response.json())
    response.raise_for_status()
    result = response.json()

    q_text = result.get("answer", "Could not generate a question.")
    return Question(topic=topic, question=q_text)

async def generate_questions_with_neuralseek(topic: str, num_questions: int = 10) -> List[Question]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "embedcode": NEURALSEEK_EMBED_CODE,
        "apikey": NEURALSEEK_API_KEY,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [_fetch_one_question(client, headers, topic) for _ in range(max(1, num_questions))]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        questions: List[Question] = [res for res in results if isinstance(res, Question)]
        
        return questions

async def validate_answer_with_neuralseek(topic: str, question_text: str, user_answer: str) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "embedcode": NEURALSEEK_EMBED_CODE,
        "apikey": NEURALSEEK_API_KEY,
    }
    
    try:
        payload = {"agent": ANSWER_VALIDATOR_AGENT, "params": [{"name": "user_answer", "value": user_answer}, {"name": "question", "value": question_text}, {"name": "chosenTopic", "value": topic}], "options": {"temperatureMod": 20, "maxTokens": 25}}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{NEURALSEEK_API_URL}/maistro", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        
    except Exception as e:
        return {"feedback": "Unable to automatically grade this answer."}
