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


# NeuralSeek API Configuration
NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL", "https://api.neuralseek.com/v1")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY", "your-api-key-here")

# NeuralSeek Agent Names - customize these based on your actual agent names
QUESTION_GENERATOR_AGENT = os.getenv("QUESTION_GENERATOR_AGENT", "question_generator_agent")
ANSWER_VALIDATOR_AGENT = os.getenv("ANSWER_VALIDATOR_AGENT", "answer_validator_agent")
CONTENT_ANALYZER_AGENT = os.getenv("CONTENT_ANALYZER_AGENT", "content_analyzer_agent")


async def call_neuralseek_agent(agent_name: str, query: str, context: str = "", parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Make async HTTP request to NeuralSeek API to invoke a specific agent
    
    Args:
        agent_name: Name of the NeuralSeek agent to invoke
        query: The query/prompt to send to the agent
        context: Optional context/background information for the agent
        parameters: Optional additional parameters for the agent
        
    Returns:
        API response as dictionary with agent's output
        
    Raises:
        httpx.HTTPError: If API request fails
        
    Example:
        response = await call_neuralseek_agent(
            agent_name="question_generator_agent",
            query="Generate 5 questions about Python",
            context=pdf_text
        )
    """
    headers = {
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Build the payload for NeuralSeek agent API
    payload = {
        "agent": agent_name,
        "query": query,
        "context": context,
        **(parameters or {})
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{NEURALSEEK_API_URL}/agent/invoke",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()


def extract_chapters_from_text(text: str) -> List[str]:
    """
    Extract chapter/section names from text using regex patterns
    
    Patterns match:
    - "Chapter 1: Introduction"
    - "Section 2.1 - Overview"
    - "1. Getting Started"
    
    Args:
        text: Text content to extract chapters from
        
    Returns:
        List of chapter names (max 10)
    """
    patterns = [
        r"Chapter\s+\d+[:\-\s]+([^\n]+)",
        r"Section\s+[\d\.]+[:\-\s]+([^\n]+)",
        r"^\d+\.\s+([A-Z][^\n]+)",
    ]
    
    chapters = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        chapters.extend(matches)
    
    # Remove duplicates and clean up
    chapters = list(set([ch.strip() for ch in chapters if len(ch.strip()) > 3]))
    
    # If no chapters found, return generic sections
    if not chapters:
        chapters = [
            "Introduction",
            "Main Content",
            "Key Concepts",
            "Advanced Topics",
            "Summary"
        ]
    
    return chapters[:10]  # Limit to 10 chapters


async def generate_questions_with_neuralseek(pdf_text: str, num_questions: int) -> List[Question]:
    """
    Generate questions using NeuralSeek Question Generator Agent
    
    This function calls the NeuralSeek API's question_generator_agent to create
    diverse study questions from PDF content.
    
    Args:
        pdf_text: Extracted text from PDF
        num_questions: Number of questions to generate
        
    Returns:
        List of Question objects
        
    Raises:
        Exception: If API call fails or response parsing fails
    """
    try:
        # Extract chapters for better organization
        chapters = extract_chapters_from_text(pdf_text)
        
        # Prepare query for NeuralSeek Question Generator Agent
        query = f"""Generate exactly {num_questions} study questions from the provided content.

Create a diverse mix of question types:
1. Short response questions (type: "short") - Open-ended questions requiring written answers
2. Multiple choice questions (type: "mcq") - Questions with exactly 4 answer options
3. Index cards (type: "index") - Key facts and information without questions

Distribute evenly across these three types.

For each question, provide:
- type: "short", "mcq", or "index"
- chapter: The most relevant chapter/section name from the content
- question: The question text (or key fact for index cards)
- options: Array of exactly 4 options (ONLY for MCQ type, null for others)

Return ONLY a valid JSON array of questions, no additional text.

Example format:
[
  {{"type": "short", "chapter": "Introduction", "question": "Explain...", "options": null}},
  {{"type": "mcq", "chapter": "Chapter 2", "question": "Which...", "options": ["A", "B", "C", "D"]}},
  {{"type": "index", "chapter": "Key Facts", "question": "Important: ...", "options": null}}
]"""
        
        # Parameters for the agent
        parameters = {
            "num_questions": num_questions,
            "temperature": 0.7,
            "max_tokens": 3000,
            "format": "json"
        }
        
        # Call NeuralSeek Question Generator Agent
        print(f"🤖 Calling NeuralSeek agent: {QUESTION_GENERATOR_AGENT}")
        response = await call_neuralseek_agent(
            agent_name=QUESTION_GENERATOR_AGENT,
            query=query,
            context=pdf_text[:8000],  # Limit context to avoid token limits
            parameters=parameters
        )
        
        print(f"✅ Received response from NeuralSeek agent")
        
        # Parse the response from NeuralSeek
        questions = _parse_neuralseek_response(response, chapters)
        
        # Ensure we have the requested number of questions
        if len(questions) < num_questions:
            print(f"⚠️  Agent returned {len(questions)} questions, expected {num_questions}")
            # Fill in with mock questions if needed
            additional_needed = num_questions - len(questions)
            questions.extend(_generate_mock_questions(pdf_text, additional_needed, chapters))
        
        return questions[:num_questions]  # Return exactly num_questions
        
    except httpx.HTTPError as e:
        print(f"❌ NeuralSeek API error: {str(e)}")
        print("⚠️  Falling back to mock question generation")
        # Fallback to mock if API fails
        chapters = extract_chapters_from_text(pdf_text)
        return _generate_mock_questions(pdf_text, num_questions, chapters)
        
    except Exception as e:
        print(f"❌ Error generating questions: {str(e)}")
        raise Exception(f"Error generating questions with NeuralSeek: {str(e)}")


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
