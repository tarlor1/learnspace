# 🤖 NeuralSeek Agent Configuration Guide

This document explains the NeuralSeek agents used by the LearnSpace backend and how to configure them.

---

## 📋 Required Agents

### 1. **Question Generator Agent**
**Environment Variable:** `QUESTION_GENERATOR_AGENT`  
**Default Name:** `question_generator_agent`

#### Purpose
Generates diverse study questions from PDF text content.

#### Input
- **Query:** Instructions for question generation (type, count, format)
- **Context:** PDF text content (up to 8000 characters)
- **Parameters:**
  - `num_questions`: Number of questions to generate
  - `temperature`: 0.7 (creativity level)
  - `max_tokens`: 3000
  - `format`: "json"

#### Expected Output
JSON array of questions:
```json
[
  {
    "type": "short",
    "chapter": "Introduction to Python",
    "question": "Explain the concept of variables in Python.",
    "options": null
  },
  {
    "type": "mcq",
    "chapter": "Data Types",
    "question": "Which of the following is a mutable data type?",
    "options": ["int", "list", "tuple", "str"]
  },
  {
    "type": "index",
    "chapter": "Key Concepts",
    "question": "Python uses dynamic typing, meaning variable types are determined at runtime.",
    "options": null
  }
]
```

#### Question Types
- **short**: Open-ended questions requiring written answers
- **mcq**: Multiple choice with exactly 4 options
- **index**: Informational cards (facts, key points)

#### Agent Configuration in NeuralSeek
1. Create a new agent named `question_generator_agent`
2. Configure system prompt:
   ```
   You are an expert educational content creator. Generate high-quality study questions 
   from provided text. Create diverse question types: short response, multiple choice, 
   and index cards. Return responses as valid JSON arrays only.
   ```
3. Set model parameters: temperature=0.7, max_tokens=3000
4. Enable JSON mode output

---

### 2. **Answer Validator Agent**
**Environment Variable:** `ANSWER_VALIDATOR_AGENT`  
**Default Name:** `answer_validator_agent`

#### Purpose
Validates and grades student answers, provides feedback and suggestions.

#### Input
- **Query:** Question text, student answer, question type
- **Context:** Original PDF content for reference (up to 4000 characters)
- **Parameters:**
  - `question_type`: "short", "mcq", or "index"
  - `temperature`: 0.3 (consistent grading)
  - `format`: "json"

#### Expected Output
```json
{
  "score": 0.85,
  "feedback": "Good answer! You correctly explained the concept of variables. Consider adding examples of different variable types to strengthen your response.",
  "is_correct": true,
  "suggestions": [
    "Add examples of int, float, and string variables",
    "Mention type inference in Python",
    "Discuss the difference between variables and constants"
  ]
}
```

#### Scoring System
- **0.0 - 0.4**: Incorrect or insufficient
- **0.5 - 0.6**: Partially correct, major gaps
- **0.7 - 0.8**: Mostly correct, minor issues
- **0.9 - 1.0**: Excellent, comprehensive answer

#### Agent Configuration in NeuralSeek
1. Create agent named `answer_validator_agent`
2. Configure system prompt:
   ```
   You are an expert educator and grader. Evaluate student answers objectively, 
   provide constructive feedback, and suggest improvements. Be fair but thorough. 
   Return responses as valid JSON objects only.
   ```
3. Set model parameters: temperature=0.3, max_tokens=1000
4. Enable JSON mode output

---

### 3. **Content Analyzer Agent**
**Environment Variable:** `CONTENT_ANALYZER_AGENT`  
**Default Name:** `content_analyzer_agent`

#### Purpose
Analyzes PDF content structure, identifies chapters, topics, and recommends optimal question distribution.

#### Input
- **Query:** Instructions to analyze content structure
- **Context:** PDF text content (up to 6000 characters)
- **Parameters:**
  - `temperature`: 0.5
  - `format`: "json"

#### Expected Output
```json
{
  "chapters": [
    {
      "title": "Introduction to Python",
      "topics": ["Variables", "Data Types", "Basic Syntax"]
    },
    {
      "title": "Control Flow",
      "topics": ["If Statements", "Loops", "Functions"]
    }
  ],
  "difficulty_level": "intermediate",
  "recommended_questions": 15,
  "summary": "This content covers fundamental Python programming concepts including variables, data types, control structures, and basic functions. Suitable for beginners with some programming experience."
}
```

#### Difficulty Levels
- **beginner**: Basic concepts, introductory material
- **intermediate**: Moderate complexity, requires some background
- **advanced**: Complex topics, assumes strong foundation

#### Agent Configuration in NeuralSeek
1. Create agent named `content_analyzer_agent`
2. Configure system prompt:
   ```
   You are an expert content analyst for educational materials. Analyze text to 
   identify structure, topics, difficulty level, and provide recommendations for 
   question generation. Return responses as valid JSON objects only.
   ```
3. Set model parameters: temperature=0.5, max_tokens=2000
4. Enable JSON mode output

---

## 🔧 Setup Instructions

### Step 1: Create Agents in NeuralSeek
1. Log into your NeuralSeek dashboard
2. Navigate to **Agents** section
3. Create three new agents with the configurations above
4. Note the exact names you give each agent

### Step 2: Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your configuration:
   ```env
   NEURALSEEK_API_URL=https://your-neuralseek-server.com/v1
   NEURALSEEK_API_KEY=your-actual-api-key
   
   # Use the exact agent names from your NeuralSeek dashboard
   QUESTION_GENERATOR_AGENT=your_question_generator_name
   ANSWER_VALIDATOR_AGENT=your_answer_validator_name
   CONTENT_ANALYZER_AGENT=your_content_analyzer_name
   ```

### Step 3: Test the Integration
Run the test script:
```bash
python test_api.py
```

Check the terminal output for:
- ✅ Successful API calls
- 🤖 Agent invocation logs
- ❌ Any errors or fallbacks to mock data

---

## 🔄 API Flow

```
User uploads PDF → Frontend extracts text → Backend receives text
                                                    ↓
                                    POST /generate-questions
                                                    ↓
                          Backend calls QUESTION_GENERATOR_AGENT
                                                    ↓
                            NeuralSeek processes request
                                                    ↓
                          Returns JSON array of questions
                                                    ↓
                        Backend parses and validates response
                                                    ↓
                          Returns questions to frontend
                                                    ↓
                              User answers questions
                                                    ↓
                               POST /submit-answer
                                                    ↓
                    (Optional) Call ANSWER_VALIDATOR_AGENT for grading
```

---

## 🐛 Troubleshooting

### Agent Not Found Error
```
❌ NeuralSeek API error: 404 - Agent not found
```
**Solution:** Verify agent names in `.env` match exactly with NeuralSeek dashboard

### Authentication Error
```
❌ NeuralSeek API error: 401 - Unauthorized
```
**Solution:** Check `NEURALSEEK_API_KEY` in `.env` file

### Timeout Error
```
❌ NeuralSeek API error: Timeout
```
**Solution:** Large PDF texts may timeout. The backend auto-limits context size.

### Invalid Response Format
```
⚠️ Unexpected response format
```
**Solution:** Ensure agents are configured to return JSON. Check agent logs in NeuralSeek.

### Fallback to Mock Data
```
⚠️ Falling back to mock question generation
```
**Cause:** API call failed, backend uses local mock generator
**Solution:** Check NeuralSeek connection and agent configuration

---

## 📊 Response Parsing

The backend handles various NeuralSeek response formats:

```python
# Format 1: Direct array
["question1", "question2"]

# Format 2: Wrapped in output field
{"output": ["question1", "question2"]}

# Format 3: Wrapped in result field
{"result": ["question1", "question2"]}

# Format 4: Stringified JSON
{"output": "[\"question1\", \"question2\"]"}
```

The `_parse_neuralseek_response()` function handles all these cases automatically.

---

## 🎯 Customization

### Change Agent Behavior
Edit the query/prompt in `utils.py`:
```python
query = f"""Your custom instructions here...
Generate {num_questions} questions...
"""
```

### Adjust Context Size
Modify context limits in `utils.py`:
```python
context=pdf_text[:8000]  # Increase or decrease as needed
```

### Add New Agents
1. Create agent in NeuralSeek
2. Add environment variable to `.env.example`
3. Create function in `utils.py`:
   ```python
   async def my_custom_agent_function(...):
       response = await call_neuralseek_agent(
           agent_name=os.getenv("MY_CUSTOM_AGENT"),
           query=...,
           context=...
       )
   ```

---

## 📝 Testing Checklist

- [ ] All three agents created in NeuralSeek
- [ ] Agent names match `.env` configuration
- [ ] API key is valid and has permissions
- [ ] API URL is correct (including /v1 or other version)
- [ ] Agents return JSON format responses
- [ ] Test script runs without errors
- [ ] Questions are generated successfully
- [ ] Answer validation works (if implemented)

---

## 🆘 Support

If you encounter issues:

1. **Check NeuralSeek Dashboard:**
   - Verify agents are active
   - Check agent execution logs
   - Test agents directly in dashboard

2. **Check Backend Logs:**
   - Look for `🤖 Calling NeuralSeek agent:` messages
   - Check for `✅ Received response` confirmations
   - Note any `❌` error messages

3. **Enable Debug Mode:**
   Add to `utils.py`:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Test API Connection:**
   ```python
   import httpx
   response = httpx.get(NEURALSEEK_API_URL + "/health")
   print(response.status_code)
   ```

---

**Last Updated:** November 8, 2025  
**Version:** 1.0.0
