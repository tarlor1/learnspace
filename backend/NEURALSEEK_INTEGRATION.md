# 🎯 LearnSpace Backend - NeuralSeek Integration Summary

## ✅ What Was Built

Your FastAPI backend now integrates with **NeuralSeek AI agents** to generate questions, validate answers, and analyze content from PDFs.

---

## 📁 Updated Files

### 1. **utils.py** - Core NeuralSeek Integration
**Key Functions:**

- `call_neuralseek_agent()` - Generic function to invoke any NeuralSeek agent
  - Handles authentication with API key
  - Sends query + context to agents
  - Returns parsed JSON response

- `generate_questions_with_neuralseek()` - Calls Question Generator Agent
  - Sends PDF text to agent
  - Requests specific number of questions
  - Parses response into Question objects
  - Falls back to mock data if API fails

- `validate_answer_with_neuralseek()` - Calls Answer Validator Agent
  - Grades student answers
  - Provides feedback and suggestions
  - Returns score (0.0-1.0) and correctness

- `analyze_content_structure()` - Calls Content Analyzer Agent
  - Identifies chapters and topics
  - Determines difficulty level
  - Recommends optimal question count

- `_parse_neuralseek_response()` - Parses various response formats
  - Handles different JSON structures
  - Validates question types
  - Ensures MCQ questions have 4 options

### 2. **.env.example** - Environment Configuration Template
```env
NEURALSEEK_API_URL=https://api.neuralseek.com/v1
NEURALSEEK_API_KEY=your-api-key-here

QUESTION_GENERATOR_AGENT=question_generator_agent
ANSWER_VALIDATOR_AGENT=answer_validator_agent
CONTENT_ANALYZER_AGENT=content_analyzer_agent
```

### 3. **AGENTS.md** - Complete Agent Documentation
- Detailed description of each agent
- Input/output specifications
- Configuration instructions
- Troubleshooting guide
- Testing checklist

### 4. **test_agents.py** - Agent Testing Script
- Tests all three agents
- Validates configuration
- Shows sample responses
- Provides troubleshooting tips

---

## 🤖 NeuralSeek Agents (Customize Names)

### Agent 1: Question Generator
**Default Name:** `question_generator_agent`  
**Purpose:** Generate study questions from PDF text  
**Output:** JSON array of questions (short/mcq/index)

### Agent 2: Answer Validator
**Default Name:** `answer_validator_agent`  
**Purpose:** Grade student answers and provide feedback  
**Output:** JSON with score, feedback, correctness

### Agent 3: Content Analyzer
**Default Name:** `content_analyzer_agent`  
**Purpose:** Analyze document structure and topics  
**Output:** JSON with chapters, difficulty, recommendations

---

## 🔄 API Request Flow

```
1. Frontend extracts PDF text
         ↓
2. POST /generate-questions with pdf_text
         ↓
3. Backend calls call_neuralseek_agent()
         ↓
4. Sends to: {NEURALSEEK_API_URL}/agent/invoke
   Payload: {
     "agent": "question_generator_agent",
     "query": "Generate 10 questions...",
     "context": "PDF text...",
     "num_questions": 10,
     "temperature": 0.7,
     "format": "json"
   }
         ↓
5. NeuralSeek agent processes request
         ↓
6. Returns: {
     "output": [
       {"type": "short", "chapter": "...", "question": "..."},
       {"type": "mcq", "chapter": "...", "question": "...", "options": [...]},
       ...
     ]
   }
         ↓
7. Backend parses with _parse_neuralseek_response()
         ↓
8. Returns formatted questions to frontend
```

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Agents in NeuralSeek
1. Log into your NeuralSeek dashboard
2. Create three agents (see AGENTS.md for details):
   - question_generator_agent
   - answer_validator_agent
   - content_analyzer_agent
3. Configure each agent to return JSON format
4. Note the exact names you use

### Step 3: Configure Environment
```bash
# Copy template
copy .env.example .env

# Edit .env and add:
# - Your NeuralSeek API URL
# - Your NeuralSeek API key
# - Your exact agent names
```

### Step 4: Test Agent Configuration
```bash
python test_agents.py
```

This will test each agent and show you if they're configured correctly.

### Step 5: Start the Server
```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000  
API Docs at: http://localhost:8000/docs

---

## 📝 Example Agent Payload

### What the backend sends to NeuralSeek:

```json
{
  "agent": "question_generator_agent",
  "query": "Generate exactly 10 study questions from the provided content...",
  "context": "Chapter 1: Introduction to Python\nPython is a programming language...",
  "num_questions": 10,
  "temperature": 0.7,
  "max_tokens": 3000,
  "format": "json"
}
```

### What NeuralSeek returns:

```json
{
  "output": [
    {
      "type": "short",
      "chapter": "Introduction to Python",
      "question": "Explain what Python is and its main uses.",
      "options": null
    },
    {
      "type": "mcq",
      "chapter": "Python Basics",
      "question": "Which of the following is a valid Python data type?",
      "options": ["int", "string", "char", "decimal"]
    },
    {
      "type": "index",
      "chapter": "Key Facts",
      "question": "Python was created by Guido van Rossum in 1991.",
      "options": null
    }
  ]
}
```

---

## 🐛 Troubleshooting

### "Agent not found" error
**Problem:** Agent name in .env doesn't match NeuralSeek  
**Solution:** Copy exact agent name from NeuralSeek dashboard

### "Unauthorized" error
**Problem:** Invalid API key  
**Solution:** Check NEURALSEEK_API_KEY in .env

### Timeout errors
**Problem:** Request took too long  
**Solution:** Reduce PDF text size (auto-limited to 8000 chars)

### Falling back to mock data
**Problem:** API call failed  
**Solution:** Check test_agents.py output for details

### Invalid response format
**Problem:** Agent not returning JSON  
**Solution:** Configure agent to use JSON mode in NeuralSeek

---

## 🎨 Customization

### Change Agent Names
Edit `.env`:
```env
QUESTION_GENERATOR_AGENT=my_custom_question_agent
```

### Adjust Context Size
Edit `utils.py`:
```python
context=pdf_text[:8000]  # Change to 10000, 5000, etc.
```

### Modify Agent Queries
Edit prompts in `utils.py` functions:
```python
query = f"""Your custom instructions here...
Generate questions with these requirements...
"""
```

### Add More Agents
1. Create function in utils.py
2. Add agent name to .env
3. Call with `call_neuralseek_agent()`

---

## 📊 Response Parsing

The backend handles multiple response formats automatically:

| Format | Example | Handled |
|--------|---------|---------|
| Direct array | `[q1, q2]` | ✅ |
| Wrapped in output | `{"output": [q1, q2]}` | ✅ |
| Wrapped in result | `{"result": [q1, q2]}` | ✅ |
| Stringified JSON | `{"output": "[q1, q2]"}` | ✅ |

---

## 🧪 Testing

### Test Individual Agents
```bash
python test_agents.py
```

### Test Full API
```bash
# Terminal 1: Start server
uvicorn main:app --reload

# Terminal 2: Run tests
python test_api.py
```

### Test from Frontend
```typescript
const response = await fetch('http://localhost:8000/generate-questions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    pdf_text: 'Your PDF content here...',
    num_questions: 10
  })
});
const data = await response.json();
console.log(data.questions); // Array of generated questions
```

---

## 📚 Documentation Files

- **README.md** - Main API documentation
- **AGENTS.md** - Detailed agent configuration guide (⭐ READ THIS FIRST)
- **QUICKSTART.md** - Quick reference guide
- **This file** - Integration summary

---

## ✨ Key Features

✅ **Real NeuralSeek Integration** - Calls actual AI agents  
✅ **Fallback to Mock** - Works even if API fails  
✅ **3 AI Agents** - Question generation, answer validation, content analysis  
✅ **Flexible Response Parsing** - Handles various JSON formats  
✅ **Error Handling** - Graceful degradation with detailed logging  
✅ **Environment Configuration** - Easy to customize agent names  
✅ **Testing Tools** - Scripts to verify configuration  
✅ **Full Documentation** - Complete setup and troubleshooting guides

---

## 🎯 Next Steps

1. **Set up agents in NeuralSeek dashboard** (see AGENTS.md)
2. **Configure .env file** with your credentials
3. **Run test_agents.py** to verify setup
4. **Start the server** with uvicorn
5. **Test from frontend** or use test_api.py
6. **Customize** agent behavior as needed

---

## 🆘 Need Help?

1. **Check AGENTS.md** - Comprehensive configuration guide
2. **Run test_agents.py** - Diagnose configuration issues
3. **Check server logs** - Look for 🤖 and ❌ messages
4. **Test in NeuralSeek dashboard** - Verify agents work there first

---

**Status:** ✅ Ready to use!  
**Last Updated:** November 8, 2025  
**Version:** 2.0.0 (NeuralSeek Integration)
