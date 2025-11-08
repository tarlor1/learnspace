# LearnSpace Backend API

FastAPI backend for PDF-based question generation, powered by NeuralSeek AI.

> **📖 See [AGENTS.md](AGENTS.md) for detailed NeuralSeek agent configuration guide**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the backend directory:

```env
NEURALSEEK_API_URL=https://api.neuralseek.com/v1
NEURALSEEK_API_KEY=your-api-key-here

# NeuralSeek Agent Names (see AGENTS.md for details)
QUESTION_GENERATOR_AGENT=question_generator_agent
ANSWER_VALIDATOR_AGENT=answer_validator_agent
CONTENT_ANALYZER_AGENT=content_analyzer_agent
```

### 3. Run the Server

```bash
uvicorn main:app --reload
```

The API will be available at: **http://localhost:8000**

### 4. View API Documentation

FastAPI automatically generates interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🤖 NeuralSeek Integration

This backend uses **three NeuralSeek agents** to power AI functionality:

1. **Question Generator Agent** - Creates study questions from PDF content
2. **Answer Validator Agent** - Grades student answers and provides feedback  
3. **Content Analyzer Agent** - Analyzes document structure and topics

**Setup Guide:** See [AGENTS.md](AGENTS.md) for complete configuration instructions.

---

## 📋 API Endpoints

### Health Check
```http
GET /
```
Returns API status and available endpoints.

---

### Generate Questions
```http
POST /generate-questions
Content-Type: application/json

{
  "pdf_text": "Your extracted PDF text here...",
  "num_questions": 10
}
```

**Response:**
```json
{
  "message": "Questions generated successfully using NeuralSeek AI",
  "num_questions": 10,
  "questions": [
    {
      "id": "uuid",
      "type": "short",
      "chapter": "Introduction",
      "question": "Explain the main concept...",
      "options": null
    },
    {
      "id": "uuid",
      "type": "mcq",
      "chapter": "Chapter 2",
      "question": "Which of the following...",
      "options": ["Option A", "Option B", "Option C", "Option D"]
    },
    {
      "id": "uuid",
      "type": "index",
      "chapter": "Key Facts",
      "question": "Important information about...",
      "options": null
    }
  ],
  "session_id": "session-uuid"
}
```

---

### Submit Answer
```http
POST /submit-answer
Content-Type: application/json

{
  "question_id": "question-uuid",
  "answer": "User's answer or selected option"
}
```

**Response:**
```json
{
  "message": "Answer submitted successfully",
  "question_id": "question-uuid",
  "answer": "User's answer",
  "timestamp": "2025-11-08T12:34:56.789Z"
}
```

---

### Get All Questions
```http
GET /questions
```

**Response:**
```json
{
  "message": "Questions retrieved successfully",
  "total_questions": 10,
  "questions": [...]
}
```

---

### Get Session Data
```http
GET /session/{session_id}
```

**Response:**
```json
{
  "session_id": "uuid",
  "num_questions": 10,
  "num_answers": 5,
  "questions": [...],
  "answers": [...],
  "created_at": "2025-11-08T12:00:00",
  "text_preview": "PDF text preview..."
}
```

---

### Get Statistics
```http
GET /stats
```

**Response:**
```json
{
  "total_sessions": 5,
  "total_questions": 50,
  "total_answers": 30,
  "questions_by_type": {
    "short_response": 17,
    "multiple_choice": 16,
    "index_cards": 17
  },
  "answer_rate": "60.0%"
}
```

---

### Reset Data (Dev Only)
```http
DELETE /reset
```

Clears all stored data. **Use only for testing!**

---

## 🏗️ Project Structure

```
backend/
├── main.py          # FastAPI app with all endpoints
├── models.py        # Pydantic models for request/response validation
├── utils.py         # NeuralSeek API integration and utilities
├── requirements.txt # Python dependencies
├── .env            # Environment variables (create this)
└── README.md       # This file
```

---

## 🔧 Question Types

The API generates three types of questions using NeuralSeek AI:

1. **Short Response** (`type: "short"`)
   - Open-ended questions
   - Require written answers
   - No multiple choice options

2. **Multiple Choice** (`type: "mcq"`)
   - 4 answer options
   - User selects one option
   - Good for testing knowledge

3. **Index Card** (`type: "index"`)
   - Informational content only
   - No question to answer
   - Key facts and concepts

---

## 🤖 NeuralSeek Integration

### Current Implementation

The backend forwards requests to NeuralSeek API with your API key. The flow is:

1. Frontend sends PDF text → Backend
2. Backend formats request → NeuralSeek API
3. NeuralSeek generates questions → Backend
4. Backend returns formatted questions → Frontend

### Mock Mode

For development without NeuralSeek API access, the `utils.py` file includes a mock question generator (`_generate_mock_questions`). This creates sample questions for testing.

### Switching to Real API

To use the actual NeuralSeek API:

1. Add your API credentials to `.env`:
   ```env
   NEURALSEEK_API_URL=https://api.neuralseek.com/v1
   NEURALSEEK_API_KEY=your-actual-api-key
   ```

2. In `utils.py`, uncomment the actual API call in `generate_questions_with_neuralseek()`:
   ```python
   # Uncomment this line:
   response = await call_neuralseek_api("/generate", payload)
   
   # Comment out this line:
   # questions = _generate_mock_questions(pdf_text, num_questions, chapters)
   ```

3. Adjust the API endpoint and payload format based on NeuralSeek's actual API documentation.

---

## 🌐 CORS Configuration

The API accepts requests from:
- http://localhost:3000 (Next.js default)
- http://127.0.0.1:3000
- http://localhost:3001
- http://localhost:3002

To add production URLs, edit `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-production-domain.com",  # Add this
    ],
    ...
)
```

---

## 💾 Data Storage

**Current:** In-memory dictionary (data lost on restart)

**For Production:**
- PostgreSQL with SQLAlchemy
- MongoDB with motor
- Redis for caching

---

## 🧪 Testing the API

### Using curl

```bash
# Generate questions
curl -X POST "http://localhost:8000/generate-questions" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_text": "Sample text about Python programming...",
    "num_questions": 5
  }'

# Get all questions
curl -X GET "http://localhost:8000/questions"

# Submit an answer
curl -X POST "http://localhost:8000/submit-answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "your-question-id",
    "answer": "My answer"
  }'
```

### Using Python requests

```python
import requests

# Generate questions
response = requests.post(
    "http://localhost:8000/generate-questions",
    json={
        "pdf_text": "Your PDF text here...",
        "num_questions": 10
    }
)
print(response.json())
```

### Using the Interactive Docs

Visit http://localhost:8000/docs and try out endpoints directly in your browser!

---

## 🔐 Environment Variables

Create a `.env` file:

```env
# NeuralSeek API Configuration
NEURALSEEK_API_URL=https://api.neuralseek.com/v1
NEURALSEEK_API_KEY=your-api-key-here

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

Load in code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📦 Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **httpx** - Async HTTP client for API calls
- **python-dotenv** - Environment variable management

---

## 🚢 Deployment

### Local Development
```bash
uvicorn main:app --reload
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📝 Next Steps

- [ ] Integrate with actual NeuralSeek API
- [ ] Add database support (PostgreSQL/MongoDB)
- [ ] Implement user authentication (JWT)
- [ ] Add question validation/grading
- [ ] Rate limiting for API endpoints
- [ ] Logging and monitoring
- [ ] Unit tests with pytest
- [ ] CI/CD pipeline

---

## 🤝 Integration with Frontend

Your Next.js frontend can call these endpoints:

```typescript
// Generate questions
const response = await fetch('http://localhost:8000/generate-questions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    pdf_text: extractedText,
    num_questions: 10
  })
});
const data = await response.json();

// Submit answer
await fetch('http://localhost:8000/submit-answer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question_id: questionId,
    answer: userAnswer
  })
});
```

---

## 📄 License

MIT

---

## 🆘 Support

For issues or questions:
1. Check API docs at `/docs`
2. Verify environment variables
3. Check server logs
4. Review NeuralSeek API documentation

**Server running?** Check http://localhost:8000/

**Need help?** Open an issue on GitHub.
