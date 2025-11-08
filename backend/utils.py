"""
Utility functions for NeuralSeek API integration and question generation

NeuralSeek Agent Configuration:
- QUESTION_GENERATOR_AGENT: Generates diverse study questions from PDF content
- ANSWER_VALIDATOR_AGENT: Validates and grades student answers
- CONTENT_ANALYZER_AGENT: Analyzes PDF text structure and extracts chapters

Agent Names (customize these in .env):
- question_generator_agent
- answer_validator_agent  
- content_analyzer_agent
"""
import os
import re
import random
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

# NeuralSeek Agent Names - customize these based on your actual agent names
QUESTION_GENERATOR_AGENT = os.getenv("QUESTION_GENERATOR_AGENT", "question_generator_agent")
ANSWER_VALIDATOR_AGENT = os.getenv("ANSWER_VALIDATOR_AGENT", "answer_validator_agent")
CONTENT_ANALYZER_AGENT = os.getenv("CONTENT_ANALYZER_AGENT", "content_analyzer_agent")

print(f"✅ Loaded NeuralSeek Config:")
print(f"   URL: {NEURALSEEK_API_URL}")
print(f"   API Key: {'*' * 20}{NEURALSEEK_API_KEY[-4:] if len(NEURALSEEK_API_KEY) > 4 else '****'}")
print(f"   Question Agent: {QUESTION_GENERATOR_AGENT}")

async def generate_questions_with_neuralseek(pdf_text: str = "", num_questions: int = 10) -> List[Question]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
    }

    print(f"\n🤖 Generating {num_questions} questions via NeuralSeek")
    print(f"📡 API URL: {NEURALSEEK_API_URL}/maistro")
    
    questions = []
    
    # Make multiple requests to generate questions one at a time
    async with httpx.AsyncClient(timeout=60) as client:
        for i in range(num_questions):
            try:
                print(f"\n🔄 Request {i+1}/{num_questions}...")
                
                # Simple payload - agent doesn't use these params but we'll send minimal data
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
                
                # Parse the single response into a Question object
                parsed_questions = _parse_single_neuralseek_response(result, i+1)
                if parsed_questions:
                    questions.extend(parsed_questions)
                    print(f"✅ Added question {i+1}")
                else:
                    print(f"⚠️  Could not parse response {i+1}, generating mock question")
                    # Add a mock question if parsing failed
                    mock_q = _generate_mock_questions(pdf_text or "Sample", 1, [f"Topic {i+1}"])
                    questions.extend(mock_q)
                
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Error on request {i+1}: {e.response.status_code}")
                print(f"❌ Response: {e.response.text[:200]}")
                # Add mock question on error
                mock_q = _generate_mock_questions(pdf_text or "Sample", 1, [f"Topic {i+1}"])
                questions.extend(mock_q)
                
            except httpx.RequestError as e:
                print(f"❌ Request Error on {i+1}: {str(e)}")
                # Add mock question on error
                mock_q = _generate_mock_questions(pdf_text or "Sample", 1, [f"Topic {i+1}"])
                questions.extend(mock_q)
            
            except Exception as e:
                print(f"❌ Unexpected error on {i+1}: {str(e)}")
                # Add mock question on error
                mock_q = _generate_mock_questions(pdf_text or "Sample", 1, [f"Topic {i+1}"])
                questions.extend(mock_q)
    
    print(f"\n✅ Total questions generated: {len(questions)}")
    return questions[:num_questions]  # Ensure we return exactly num_questions


def _parse_single_neuralseek_response(response: Dict[str, Any], question_num: int) -> List[Question]:
    """
    Parse a single NeuralSeek response into Question object(s).
    Handles various response formats the API might return.
    """
    questions = []
    
    try:
        print(f"🔍 Parsing response structure: {list(response.keys())}")
        
        # Try to extract the actual content from various possible response structures
        data = response
        
        # Check for common wrapper keys
        if 'output' in response:
            data = response['output']
            print(f"   Found 'output' key")
        elif 'result' in response:
            data = response['result']
            print(f"   Found 'result' key")
        elif 'question' in response:
            data = response['question']
            print(f"   Found 'question' key")
        elif 'questions' in response:
            data = response['questions']
            print(f"   Found 'questions' key")
        elif 'answer' in response:
            data = response['answer']
            print(f"   Found 'answer' key")
        elif 'text' in response:
            data = response['text']
            print(f"   Found 'text' key")
        
        # If data is a string, try to parse as JSON
        if isinstance(data, str):
            print(f"   Data is string, attempting JSON parse...")
            try:
                data = json.loads(data)
            except:
                # If not JSON, treat the string itself as the question
                print(f"   Not JSON, using as question text")
                question = Question(
                    type="short",
                    chapter=f"Section {question_num}",
                    question=data[:500] if len(data) > 500 else data,
                    options=None
                )
                questions.append(question)
                return questions
        
        # If data is a list, process each item
        if isinstance(data, list):
            print(f"   Data is list with {len(data)} items")
            for idx, item in enumerate(data):
                try:
                    if isinstance(item, str):
                        # String item - create a short response question
                        q = Question(
                            type="short",
                            chapter=f"Section {question_num}",
                            question=item[:500],
                            options=None
                        )
                    elif isinstance(item, dict):
                        # Dict item - extract fields
                        q = Question(
                            type=item.get('type', 'short'),
                            chapter=item.get('chapter', f"Section {question_num}"),
                            question=item.get('question', item.get('text', f"Question {question_num}")),
                            options=item.get('options')
                        )
                    else:
                        continue
                    
                    questions.append(q)
                    print(f"   ✅ Parsed item {idx+1}: [{q.type}] {q.question[:60]}...")
                except Exception as e:
                    print(f"   ⚠️  Error parsing list item {idx}: {e}")
                    continue
        
        # If data is a dict with question-like fields
        elif isinstance(data, dict):
            print(f"   Data is dict with keys: {list(data.keys())}")
            
            # Try to extract question text from various possible fields
            question_text = (
                data.get('question') or 
                data.get('text') or 
                data.get('content') or
                data.get('answer') or
                json.dumps(data)[:200]  # Last resort: stringify the dict
            )
            
            q = Question(
                type=data.get('type', 'short'),
                chapter=data.get('chapter', f"Section {question_num}"),
                question=question_text,
                options=data.get('options')
            )
            questions.append(q)
            print(f"   ✅ Created question: [{q.type}] {q.question[:60]}...")
        
        # If data is some other type, convert to string and use as question
        else:
            print(f"   Data is {type(data)}, converting to question")
            q = Question(
                type="short",
                chapter=f"Section {question_num}",
                question=str(data)[:500],
                options=None
            )
            questions.append(q)
        
        if questions:
            print(f"   ✅ Successfully parsed {len(questions)} question(s)")
        else:
            print(f"   ⚠️  No questions extracted from response")
        
    except Exception as e:
        print(f"   ❌ Error parsing response: {e}")
        import traceback
        traceback.print_exc()
    
    return questions


def _generate_mock_questions(pdf_text: str, num_questions: int, chapters: List[str]) -> List[Question]:
    """
    Mock question generation for development/testing
    Replace this with actual NeuralSeek API integration
    
    Args:
        pdf_text: Source text
        num_questions: Number of questions to generate
        chapters: List of chapter names
        
    Returns:
        List of Question objects
    """
    # Extract some sentences for question content
    sentences = [s.strip() for s in pdf_text.split('.') if len(s.strip()) > 20]
    sentences = sentences[:50] if sentences else ["Sample content"]
    
    questions = []
    question_types = ["short", "mcq", "index"]
    
    # Question templates
    short_templates = [
        "Explain the concept of {}.",
        "What is the significance of {}?",
        "Describe the main points about {}.",
        "How does {} relate to the topic?",
        "Define {} in your own words."
    ]
    
    mcq_templates = [
        "Which of the following best describes {}?",
        "What is the main purpose of {}?",
        "According to the text, {} is:",
        "Which statement about {} is most accurate?"
    ]
    
    index_templates = [
        "Key Information: {}",
        "Important Note: {}",
        "Remember: {}",
        "Core Concept: {}"
    ]
    
    for i in range(num_questions):
        q_type = question_types[i % 3]
        chapter = random.choice(chapters)
        content = random.choice(sentences)[:80]
        
        if q_type == "short":
            question = Question(
                type="short",
                chapter=chapter,
                question=random.choice(short_templates).format(content),
                options=None
            )
        
        elif q_type == "mcq":
            options = [
                f"{content[:40]}",
                f"Alternative explanation of {content[:25]}",
                f"Related concept to {content[:25]}",
                "None of the above"
            ]
            random.shuffle(options)
            
            question = Question(
                type="mcq",
                chapter=chapter,
                question=random.choice(mcq_templates).format(content[:40]),
                options=options
            )
        
        else:  # index card
            question = Question(
                type="index",
                chapter=chapter,
                question=random.choice(index_templates).format(content),
                options=None
            )
        
        questions.append(question)
    
    return questions


def _parse_neuralseek_response(response: Dict[str, Any], fallback_chapters: List[str]) -> List[Question]:
    """
    Parse NeuralSeek agent response into Question objects
    
    Args:
        response: Raw response from NeuralSeek agent
        fallback_chapters: Fallback chapter names if not provided
        
    Returns:
        List of Question objects
    """
    questions = []
    
    try:
        # NeuralSeek response might be in different formats
        # Try to extract the questions array from common response structures
        
        # Check if response has 'output' or 'result' field
        if 'output' in response:
            data = response['output']
        elif 'result' in response:
            data = response['result']
        elif 'questions' in response:
            data = response['questions']
        else:
            data = response
        
        # If data is a string, try to parse as JSON
        if isinstance(data, str):
            data = json.loads(data)
        
        # If data is not a list, try to extract it
        if not isinstance(data, list):
            if 'questions' in data:
                data = data['questions']
            else:
                print(f"⚠️  Unexpected response format: {type(data)}")
                return []
        
        # Parse each question
        for item in data:
            try:
                # Handle different response formats
                q_type = item.get('type', 'short')
                chapter = item.get('chapter', random.choice(fallback_chapters))
                question_text = item.get('question', '') or item.get('text', '')
                options = item.get('options')
                
                # Validate question type
                if q_type not in ['short', 'mcq', 'index']:
                    q_type = 'short'
                
                # Ensure MCQ has options
                if q_type == 'mcq' and not options:
                    continue  # Skip invalid MCQ
                
                # Ensure non-MCQ doesn't have options
                if q_type != 'mcq':
                    options = None
                
                question = Question(
                    type=q_type,
                    chapter=chapter,
                    question=question_text,
                    options=options
                )
                questions.append(question)
                
            except Exception as e:
                print(f"⚠️  Error parsing question: {str(e)}")
                continue
        
        print(f"✅ Successfully parsed {len(questions)} questions from NeuralSeek response")
        return questions
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Error parsing NeuralSeek response: {str(e)}")
        return []


async def validate_answer_with_neuralseek(
    question_text: str, 
    user_answer: str, 
    context: str,
    question_type: str = "short"
) -> Dict[str, Any]:
    """
    Validate and grade user's answer using NeuralSeek Answer Validator Agent
    
    This function is useful for grading short response questions and providing
    detailed feedback to students.
    
    Args:
        question_text: The original question text
        user_answer: User's submitted answer
        context: Original PDF context/content for reference
        question_type: Type of question ("short", "mcq", "index")
        
    Returns:
        Validation result with score, feedback, and correctness
        
    Example:
        result = await validate_answer_with_neuralseek(
            question_text="Explain Python variables",
            user_answer="Variables store data",
            context=pdf_text,
            question_type="short"
        )
        # Returns: {"score": 0.85, "feedback": "Good answer...", "is_correct": True}
    """
    try:
        query = f"""Evaluate the following student answer:

Question: {question_text}
Student Answer: {user_answer}
Question Type: {question_type}

Provide:
1. Score (0.0 to 1.0)
2. Detailed feedback
3. Whether the answer is correct (true/false)
4. Suggestions for improvement

Return as JSON:
{{
  "score": 0.85,
  "feedback": "Your answer is...",
  "is_correct": true,
  "suggestions": ["Add more detail about...", "Consider mentioning..."]
}}"""
        
        parameters = {
            "question_type": question_type,
            "temperature": 0.3,  # Lower temperature for more consistent grading
            "format": "json"
        }
        
        print(f"🤖 Calling NeuralSeek agent: {ANSWER_VALIDATOR_AGENT}")
        response = await call_neuralseek_agent(
            agent_name=ANSWER_VALIDATOR_AGENT,
            query=query,
            context=context[:4000],  # Limit context
            parameters=parameters
        )
        
        # Parse the validation response
        if 'output' in response:
            result = response['output']
        elif 'result' in response:
            result = response['result']
        else:
            result = response
        
        if isinstance(result, str):
            result = json.loads(result)
        
        print(f"✅ Answer validated with score: {result.get('score', 'N/A')}")
        return result
        
    except Exception as e:
        print(f"❌ Error validating answer: {str(e)}")
        # Return default validation result if API fails
        return {
            "score": 0.5,
            "feedback": "Unable to automatically grade this answer. Manual review recommended.",
            "is_correct": None,
            "suggestions": []
        }


async def analyze_content_structure(pdf_text: str) -> Dict[str, Any]:
    """
    Analyze PDF content structure using NeuralSeek Content Analyzer Agent
    
    This function identifies chapters, key topics, difficulty level, and optimal
    question distribution for the content.
    
    Args:
        pdf_text: Extracted text from PDF
        
    Returns:
        Analysis result with chapters, topics, and recommendations
        
    Example:
        analysis = await analyze_content_structure(pdf_text)
        # Returns: {
        #   "chapters": [...],
        #   "key_topics": [...],
        #   "difficulty_level": "intermediate",
        #   "recommended_questions": 15
        # }
    """
    try:
        query = """Analyze this educational content and provide:

1. List of chapters/sections with titles
2. Key topics covered in each section
3. Overall difficulty level (beginner/intermediate/advanced)
4. Recommended number of questions for this content
5. Content summary

Return as JSON:
{
  "chapters": [{"title": "...", "topics": [...]}],
  "difficulty_level": "intermediate",
  "recommended_questions": 15,
  "summary": "This content covers..."
}"""
        
        parameters = {
            "temperature": 0.5,
            "format": "json"
        }
        
        print(f"🤖 Calling NeuralSeek agent: {CONTENT_ANALYZER_AGENT}")
        response = await call_neuralseek_agent(
            agent_name=CONTENT_ANALYZER_AGENT,
            query=query,
            context=pdf_text[:6000],
            parameters=parameters
        )
        
        # Parse the analysis response
        if 'output' in response:
            result = response['output']
        elif 'result' in response:
            result = response['result']
        else:
            result = response
        
        if isinstance(result, str):
            result = json.loads(result)
        
        print(f"✅ Content analyzed: {result.get('difficulty_level', 'N/A')} level")
        return result
        
    except Exception as e:
        print(f"❌ Error analyzing content: {str(e)}")
        # Return basic analysis if API fails
        chapters = extract_chapters_from_text(pdf_text)
        return {
            "chapters": [{"title": ch, "topics": []} for ch in chapters],
            "difficulty_level": "intermediate",
            "recommended_questions": 10,
            "summary": "Content analysis unavailable."
        }
