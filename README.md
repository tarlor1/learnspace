# 📚 LearnSpace

An intelligent learning platform that generates personalized practice questions from your documents using AI-powered knowledge graphs and natural language processing.

## 🌟 Overview

LearnSpace transforms your PDF documents into an interactive study experience. Upload your textbooks, research papers, or study materials, and the system automatically generates relevant practice questions tailored to the content. The platform uses a sophisticated GraphRAG (Graph Retrieval-Augmented Generation) architecture combined with NeuralSeek AI agents to create contextually relevant questions.

## ✨ Key Features

- **📄 PDF Document Upload**: Upload and process PDF documents with automatic text extraction and chunking
- **🧠 AI-Powered Question Generation**: Generate questions from actual document content using NeuralSeek mAIstro agents
- **🔄 Infinite Scrolling**: Continuously generate new practice questions as you scroll
- **📊 Knowledge Graph**: Neo4j graph database stores document chunks, concepts, and semantic relationships
- **🎯 Context-Aware Learning**: Questions are generated from relevant chunks of your documents
- **🔐 Secure Authentication**: Auth0 integration for secure user authentication
- **⚡ Real-time Processing**: Fast document processing with asynchronous operations

## 🏗️ Architecture

### Technology Stack

#### Backend
- **FastAPI**: Modern, high-performance Python web framework
- **PostgreSQL (Supabase)**: Primary database for users, documents, and questions
- **Neo4j (AuraDB)**: Graph database for document chunks and semantic relationships
- **NeuralSeek mAIstro API**: AI agents for topic generation and question creation
- **Sentence Transformers**: 384-dimensional embeddings (all-MiniLM-L6-v2)
- **SQLAlchemy**: ORM for database operations

#### Frontend
- **Next.js 16**: React framework with App Router
- **React 19**: Latest React features
- **TanStack Query v5**: Data fetching and caching
- **Auth0**: Authentication provider
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **shadcn/ui**: Beautiful, accessible UI components

### System Architecture

```
┌─────────────┐
│   Frontend  │
│  (Next.js)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│   FastAPI   │◄────►│  PostgreSQL  │
│   Backend   │      │  (Supabase)  │
└──────┬──────┘      └──────────────┘
       │
       ├────────────┐
       │            │
       ▼            ▼
┌──────────┐  ┌─────────────┐
│  Neo4j   │  │ NeuralSeek  │
│  AuraDB  │  │   mAIstro   │
└──────────┘  └─────────────┘
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL** (or Supabase account)
- **Neo4j** (or Neo4j AuraDB account)
- **NeuralSeek mAIstro** account
- **Auth0** account

### Environment Variables

#### Backend (.env)

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Neo4j
NEO4J_URI=bolt://your-neo4j-instance:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# NeuralSeek
NEURALSEEK_API_URL=https://your-instance.neuralseek.com
NEURALSEEK_API_KEY=your-api-key
NEURALSEEK_INSTANCE_ID=your-instance-id
MAKE_QUESTION_AGENT=question_maker
QUESTION_GENERATOR_AGENT=topic_generator
ANSWER_VALIDATOR_AGENT=answer_validator_agent

# Auth0
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-audience

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Frontend (.env.local)

Create a `.env.local` file in the `frontend/learnspace/` directory:

```env
# Auth0
AUTH0_SECRET=your-auth0-secret
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=your-api-audience

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Installation

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell)
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if applicable)
# python migrate.py

# Start the server
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend/learnspace

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📖 Usage

### 1. Upload Documents

1. Navigate to the upload page
2. Select a PDF document from your computer
3. Click "Upload" to process the document
4. The system will:
   - Extract text from the PDF
   - Chunk the content (2000 characters per chunk, 200 char overlap)
   - Generate embeddings using Sentence Transformers
   - Store chunks in Neo4j with semantic relationships
   - Create symbolic chapters every 30 chunks

### 2. Study with AI-Generated Questions

1. Navigate to the Study page
2. Questions will automatically generate from your documents
3. The system:
   - Fetches random chunks from your uploaded documents (Neo4j)
   - Uses the `topic_generator` agent to extract 5 topics from the chunks
   - For each topic, calls the `question_maker` agent to generate a question
   - Presents questions in an infinite scroll format

### 3. Answer Questions

1. Read the question presented in the card
2. Type your answer in the text field
3. Submit your answer for AI validation
4. Receive instant feedback on your response

## 🔧 API Endpoints

### Documents

- `GET /documents` - List user's documents
- `POST /upload` - Upload a new PDF document
- `DELETE /documents/{id}` - Delete a document

### Questions

- `POST /generate-questions` - Generate questions for study session
- `POST /generate-question` - Generate a single question for specific topic
- `POST /generate-random-questions` - Generate questions from random chunks
- `POST /submit-answer` - Submit and validate an answer

### Authentication

- `GET /auth/verify` - Verify user authentication
- `GET /api/auth/token` - Get access token

## 🧪 Testing

### Backend Tests

```bash
cd backend
python test_neuralseek_agent.py
```

### Frontend Tests

```bash
cd frontend/learnspace
npm run test
```

## 📊 Database Schema

### PostgreSQL (Supabase)

- **UserProfile**: User account information
- **Document**: Uploaded documents metadata
- **Chapter**: Symbolic chapters within documents
- **Question**: Generated questions with JSONB content

### Neo4j Graph

- **Document**: Document nodes with metadata
- **Chunk**: Text chunks with 384d embeddings
- **Concept**: Extracted concepts from content
- **Relationships**: CONTAINS, NEXT_CHUNK, RELATES_TO

## 🤖 NeuralSeek Agents

### topic_generator
- **Input**: Relevant text chunks
- **Output**: JSON array of 5 topics
- **Format**: `{"topic": ["Topic 1", "Topic 2", ...]}`

### question_maker
- **Input**: Relevant text chunks and topic
- **Output**: Structured question
- **Format**:
```json
{
  "topic": "Topic Name",
  "correct_answer": "Expected answer",
  "content": {
    "type": "short_response",
    "text": "Question text"
  }
}
```

### answer_validator_agent
- **Input**: Question, user answer, correct answer
- **Output**: Validation result with feedback

## 🎨 UI Components

Built with shadcn/ui and Radix UI:
- **IndexCard**: Flashcard-style review
- **MCQCard**: Multiple choice questions
- **ShortResponseCard**: Open-ended questions
- **Navbar**: Navigation with authentication
- **Theme Provider**: Dark/light mode support

## 🔐 Security

- **Auth0 Integration**: Industry-standard authentication
- **JWT Tokens**: Secure API access
- **User Isolation**: Each user can only access their own documents
- **CORS Protection**: Configured origins for API access
- **Environment Variables**: Sensitive data stored in .env files

### Project Structure

```
learnspace/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── routes/
│   │   ├── questions.py        # Question generation endpoints
│   │   └── upload.py           # Document upload endpoints
│   ├── database/
│   │   ├── connection.py       # Database connections
│   │   ├── models/             # SQLAlchemy models
│   │   └── upload.py           # GraphRAG indexer
│   ├── utils.py                # NeuralSeek integration
│   ├── auth.py                 # Auth0 authentication
│   └── requirements.txt
│
└── frontend/learnspace/
    ├── app/
    │   ├── page.tsx            # Home page (redirects to /study)
    │   ├── layout.tsx          # Root layout
    │   └── study/              # Study page route
    ├── components/
    │   ├── StudyPage.tsx       # Main study component
    │   ├── Navbar.tsx          # Navigation
    │   └── cards/              # Question card components
    ├── lib/
    │   ├── api.ts              # API client
    │   └── utils.ts            # Utility functions
    └── package.json
```

### Chunking Strategy

- **Chunk Size**: 2000 characters
- **Overlap**: 200 characters (10%)
- **Symbolic Chapters**: Created every 30 chunks
- **Embeddings**: 384-dimensional vectors using all-MiniLM-L6-v2

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **NeuralSeek** for AI agent capabilities
- **Auth0** for authentication infrastructure
- **Neo4j** for graph database technology
- **Vercel** for Next.js framework
- **shadcn** for beautiful UI components

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, Next.js, and AI