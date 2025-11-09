"""
Hybrid GraphRAG Upload Module
Implements the PDF-to-Graph pipeline with document isolation
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from google import genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database.models.document import Document
from database.models.chapter import Chapter

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, fast and efficient
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50  # overlap between chunks

# Initialize clients
client = genai.Client(api_key=GEMINI_API_KEY)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print(f"✅ Initialized Hybrid GraphRAG Module")
print(f"   Embedding Model: {EMBEDDING_MODEL} ({embedding_model.get_sentence_embedding_dimension()} dimensions)")
print(f"   Neo4j URI: {NEO4J_URI}")


class PDFProcessor:
    """Handles PDF text extraction and chunking"""

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """Extract all text from a PDF file"""
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundaries
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # Only break if it's not too early
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return [c for c in chunks if c]  # Filter empty chunks


class ConceptExtractor:
    """Uses Gemini to extract key concepts from text chunks"""

    @staticmethod
    def extract_concepts(chunk_text: str, max_concepts: int = 5) -> List[str]:
        """Extract key concepts from a text chunk using Gemini"""
        try:
            prompt = f"""Extract the {max_concepts} most important concepts, terms, or topics from this text.
Return ONLY a comma-separated list of concepts, nothing else.

Text: {chunk_text[:500]}

Concepts:"""

            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )

            if response.text:
                concepts_text = response.text.strip()
                concepts = [c.strip() for c in concepts_text.split(',')]
                return concepts[:max_concepts]
            return []

        except Exception as e:
            # Rate limit or quota exceeded - skip concept extraction
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"⚠️  Gemini quota exceeded - skipping concept extraction (search still works!)")
            else:
                print(f"⚠️  Concept extraction failed: {e}")
            return []


class GraphRAGIndexer:
    """Manages Neo4j graph creation and vector indexing"""

    def __init__(self, extract_concepts: bool = True):
        self.driver = neo4j_driver
        self.embedding_model = embedding_model
        self.concept_extractor = ConceptExtractor()
        self.extract_concepts_enabled = extract_concepts

    def create_vector_index(self):
        """Create vector index for chunk embeddings (run once)"""
        with self.driver.session() as session:
            try:
                session.run("""
                CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {
                  indexConfig: {
                    `vector.dimensions`: 384,
                    `vector.similarity_function`: 'cosine'
                  }
                }
                """)
                print("✅ Vector index created/verified")
            except Exception as e:
                print(f"⚠️  Vector index creation: {e}")

    def index_document(
        self,
        document_id: str,
        chunks: List[str],
        document_name: str,
        chapter_id: Optional[str] = None
    ) -> int:
        """
        Index all chunks from a document into Neo4j

        Phase 1: The Indexing Pipeline
        - Creates Document node
        - Creates Chunk nodes with embeddings
        - Extracts and links Concepts
        - Maintains document isolation via document_id
        - Stores chapter_id for difficulty tracking

        Args:
            document_id: UUID of the document
            chunks: List of text chunks
            document_name: Name of the document
            chapter_id: Optional chapter ID to associate with chunks

        Returns: Number of chunks indexed
        """
        indexed_count = 0

        with self.driver.session() as session:
            # Step 1: Create root Document node
            session.run("""
            MERGE (d:Document {id: $doc_id})
            SET d.name = $name, d.created_at = datetime()
            """, doc_id=document_id, name=document_name)

            print(f"📚 Created Document node: {document_id}")

            # Step 2: Process each chunk
            for i, chunk_text in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.embedding_model.encode(chunk_text).tolist()

                    # Extract concepts (optional - can skip if quota exceeded)
                    concepts = []
                    if self.extract_concepts_enabled:
                        concepts = self.concept_extractor.extract_concepts(chunk_text)

                    # Create Chunk node and link to Document
                    session.run("""
                    MATCH (d:Document {id: $doc_id})
                    CREATE (c:Chunk {
                        id: $chunk_id,
                        text: $text,
                        embedding: $embedding,
                        document_id: $doc_id,
                        chapter_id: $chapter_id,
                        chunk_index: $index,
                        created_at: datetime()
                    })
                    CREATE (c)-[:PART_OF]->(d)
                    """,
                        doc_id=document_id,
                        chunk_id=str(uuid.uuid4()),
                        text=chunk_text,
                        embedding=embedding,
                        chapter_id=chapter_id,
                        index=i
                    )

                    # Link concepts
                    if concepts:
                        session.run("""
                        MATCH (c:Chunk {document_id: $doc_id, chunk_index: $index})
                        WITH c
                        UNWIND $concepts AS concept_name
                        MERGE (con:Concept {name: concept_name})
                        CREATE (c)-[:MENTIONS]->(con)
                        """, doc_id=document_id, index=i, concepts=concepts)

                    indexed_count += 1

                    if (i + 1) % 10 == 0:
                        print(f"   Indexed {i + 1}/{len(chunks)} chunks...")

                except Exception as e:
                    print(f"⚠️  Error indexing chunk {i}: {e}")
                    continue

        print(f"✅ Indexed {indexed_count} chunks for document {document_id}")
        return indexed_count

    def query_document(
        self,
        document_id: str,
        query_text: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query a specific document using vector similarity

        Phase 2: The Querying Pipeline
        - Filters by document_id FIRST
        - Then performs vector search ONLY within that document
        - Returns top_k most relevant chunks

        This ensures answers for 'Book A' never come from 'Book B'
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query_text).tolist()

        with self.driver.session() as session:
            result = session.run("""
            // Step 1: Find the root Document node
            MATCH (d:Document {id: $doc_id})

            // Step 2: Find all chunks that are PART_OF this document
            WITH d
            MATCH (c:Chunk)-[:PART_OF]->(d)

            // Step 3: Vector search ONLY within these chunks
            CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_vector)
            YIELD node, score
            WHERE node = c  // Magic filter - ensures isolation!

            // Step 4: Return the most relevant chunks
            RETURN node.text AS text,
                   node.chunk_index AS chunk_index,
                   node.chapter_id AS chapter_id,
                   score
            ORDER BY score DESC
            """, doc_id=document_id, query_vector=query_embedding, top_k=top_k)

            chunks = []
            for record in result:
                chunks.append({
                    "text": record["text"],
                    "chunk_index": record["chunk_index"],
                    "chapter_id": record["chapter_id"],
                    "score": record["score"]
                })

            return chunks

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()


class DocumentUploadPipeline:
    """
    Main pipeline for processing PDF uploads
    Orchestrates: PDF → Chunks → Graph → Vector Index
    """

    def __init__(self, db_session: Session, extract_concepts: bool = False):
        """
        Args:
            db_session: SQLAlchemy session
            extract_concepts: Whether to extract concepts using Gemini (requires quota)
                             Set to False to skip concept extraction and avoid rate limits
        """
        self.db = db_session
        self.pdf_processor = PDFProcessor()
        self.indexer = GraphRAGIndexer(extract_concepts=extract_concepts)

        # Ensure vector index exists
        self.indexer.create_vector_index()

    def process_upload(
        self,
        pdf_bytes: bytes,
        filename: str,
        user_id: str,
        storage_url: str
    ) -> Document:
        """
        Complete upload pipeline:
        1. Create Document record in Postgres
        2. Extract text from PDF
        3. Chunk the text
        4. Index chunks in Neo4j with embeddings
        5. Update Document status

        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename
            user_id: Auth0 user ID (owner)
            storage_url: URL where PDF is stored (e.g., Supabase Storage)

        Returns:
            Document: The created Document record
        """
        print(f"\n🚀 Starting upload pipeline for: {filename}")

        # Phase 1.1: Create Relational Record
        doc = Document(
            owner_id=user_id,
            name=filename,
            storage_url=storage_url,
            status="processing"
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        print(f"📝 Created Document record: {doc.id}")

        try:
            # Phase 1.2: Chunk the PDF
            text = self.pdf_processor.extract_text_from_pdf(pdf_bytes)
            chunks = self.pdf_processor.chunk_text(text)

            print(f"📄 Extracted {len(chunks)} chunks from PDF")

            # Phase 1.3: Build the Graph + Vector Index
            indexed_count = self.indexer.index_document(
                document_id=str(doc.id),
                chunks=chunks,
                document_name=filename
            )

            # Update status
            self.db.query(Document).filter(Document.id == doc.id).update({"status": "ready"})
            self.db.commit()
            self.db.refresh(doc)

            print(f"✅ Upload complete: {filename} ({indexed_count} chunks)")
            return doc

        except Exception as e:
            print(f"❌ Upload failed: {e}")
            self.db.query(Document).filter(Document.id == doc.id).update({"status": "error"})
            self.db.commit()
            raise

    def generate_question_from_document(
        self,
        document_id: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a question using GraphRAG query

        Args:
            document_id: UUID of the document
            topic: Optional topic/query (if None, uses generic query)

        Returns:
            Dict with question details
        """
        # Default query if no topic provided
        query = topic or "What are the main concepts in this document?"

        # Query the graph for relevant chunks
        relevant_chunks = self.indexer.query_document(
            document_id=document_id,
            query_text=query,
            top_k=5
        )

        if not relevant_chunks:
            raise ValueError(f"No chunks found for document {document_id}")

        # Combine chunks as context
        context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])

        # Generate question using Gemini
        prompt = f"""Based on the following content, generate ONE multiple-choice question.

Content:
{context[:2000]}

Generate a JSON response with this structure:
{{
  "question": "The question text",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "correct_answer": "A",
  "explanation": "Why this is correct"
}}"""

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )

            # Parse response (simplified - add proper JSON parsing)
            return {
                "document_id": document_id,
                "question": response.text,
                "context_chunks": len(relevant_chunks),
                "relevant_chunks": relevant_chunks
            }

        except Exception as e:
            print(f"❌ Question generation failed: {e}")
            raise


# Convenience function for FastAPI route
def upload_pdf_to_graphrag(
    pdf_bytes: bytes,
    filename: str,
    user_id: str,
    storage_url: str,
    db_session: Session
) -> Document:
    """
    Convenience wrapper for upload pipeline
    Use this in your FastAPI /upload endpoint
    """
    pipeline = DocumentUploadPipeline(db_session)
    return pipeline.process_upload(pdf_bytes, filename, user_id, storage_url)