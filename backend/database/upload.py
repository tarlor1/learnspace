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
load_dotenv("../.env")

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, fast and efficient
CHUNK_SIZE = 2000  # characters per chunk (roughly 400-500 words, or 1-2 paragraphs)
CHUNK_OVERLAP = 200  # overlap between chunks (10% overlap for context continuity)

# Initialize clients
client = genai.Client(api_key=GEMINI_API_KEY)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print(f"✅ Initialized Hybrid GraphRAG Module")
print(
    f"   Embedding Model: {EMBEDDING_MODEL} ({embedding_model.get_sentence_embedding_dimension()} dimensions)"
)
print(f"   Neo4j URI: {NEO4J_URI}")


class PDFProcessor:
    """Handles PDF text extraction and chunking"""

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """Extract all text from a PDF file"""
        print(f"📖 Extracting text from PDF...")
        print(f"   PDF size: {len(pdf_bytes)} bytes")

        reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        print(f"   Total pages: {total_pages}")

        text = ""
        for i, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            text += page_text + "\n"

            # Progress indicator every 10 pages
            if i % 10 == 0 or i == total_pages:
                print(
                    f"   📄 Extracted {i}/{total_pages} pages ({len(text)} chars so far)"
                )

        print(f"✅ PDF extraction complete: {len(text)} characters extracted")
        return text

    @staticmethod
    def chunk_text(
        text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
    ) -> List[str]:
        """Split text into overlapping chunks"""
        print(f"📝 Starting text chunking...")
        print(f"   Text length: {len(text)} characters")
        print(f"   Chunk size: {chunk_size}, Overlap: {overlap}")

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundaries
            if end < text_length:
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # Only break if it's not too early
                    chunk = chunk[: break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

            # Progress indicator every 50 chunks
            if len(chunks) % 50 == 0:
                progress = (start / text_length) * 100
                print(
                    f"   📊 Chunking progress: {len(chunks)} chunks created ({progress:.1f}%)"
                )

        filtered_chunks = [c for c in chunks if c]
        print(f"✅ Chunking complete: {len(filtered_chunks)} chunks created")
        return filtered_chunks


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
                model="gemini-2.0-flash-exp", contents=prompt
            )

            if response.text:
                concepts_text = response.text.strip()
                concepts = [c.strip() for c in concepts_text.split(",")]
                return concepts[:max_concepts]
            return []

        except Exception as e:
            # Rate limit or quota exceeded - skip concept extraction
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(
                    f"⚠️  Gemini quota exceeded - skipping concept extraction (search still works!)"
                )
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
                session.run(
                    """
                CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {
                  indexConfig: {
                    `vector.dimensions`: 384,
                    `vector.similarity_function`: 'cosine'
                  }
                }
                """
                )
                print("✅ Vector index created/verified")
            except Exception as e:
                print(f"⚠️  Vector index creation: {e}")

    def index_document(
        self,
        document_id: str,
        chunks: List[str],
        document_name: str,
        chapter_id: Optional[str] = None,
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
            session.run(
                """
            MERGE (d:Document {id: $doc_id})
            SET d.name = $name, d.created_at = datetime()
            """,
                doc_id=document_id,
                name=document_name,
            )

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
                    session.run(
                        """
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
                        index=i,
                    )

                    # Link concepts
                    if concepts:
                        session.run(
                            """
                        MATCH (c:Chunk {document_id: $doc_id, chunk_index: $index})
                        WITH c
                        UNWIND $concepts AS concept_name
                        MERGE (con:Concept {name: concept_name})
                        CREATE (c)-[:MENTIONS]->(con)
                        """,
                            doc_id=document_id,
                            index=i,
                            concepts=concepts,
                        )

                    indexed_count += 1

                    if (i + 1) % 10 == 0:
                        print(f"   Indexed {i + 1}/{len(chunks)} chunks...")

                except Exception as e:
                    print(f"⚠️  Error indexing chunk {i}: {e}")
                    continue

        print(f"✅ Indexed {indexed_count} chunks for document {document_id}")
        return indexed_count

    def query_document(
        self, document_id: str, query_text: str, top_k: int = 5
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
            result = session.run(
                """
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
            """,
                doc_id=document_id,
                query_vector=query_embedding,
                top_k=top_k,
            )

            chunks = []
            for record in result:
                chunks.append(
                    {
                        "text": record["text"],
                        "chunk_index": record["chunk_index"],
                        "chapter_id": record["chapter_id"],
                        "score": record["score"],
                    }
                )

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

    def _create_symbolic_chapters(
        self, chunks: List[str], document_id: str, chunks_per_chapter: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Create symbolic chapters by splitting chunks into groups and generating summaries.

        Args:
            chunks: List of text chunks
            document_id: Document UUID
            chunks_per_chapter: Number of chunks per chapter (default: 30)

        Returns:
            List of chapter data dicts with id, name, summary, start_idx, end_idx
        """
        print(f"\n📚 Creating symbolic chapters...")
        print(f"   Total chunks: {len(chunks)}")
        print(f"   Chunks per chapter: {chunks_per_chapter}")

        chapters_data = []
        total_chunks = len(chunks)
        estimated_chapters = (
            total_chunks + chunks_per_chapter - 1
        ) // chunks_per_chapter
        print(f"   Estimated chapters: {estimated_chapters}")

        for chapter_num in range(0, total_chunks, chunks_per_chapter):
            start_idx = chapter_num
            end_idx = min(chapter_num + chunks_per_chapter, total_chunks)
            chapter_chunks = chunks[start_idx:end_idx]

            current_chapter = len(chapters_data) + 1
            print(
                f"\n   🔄 Processing chapter {current_chapter}/{estimated_chapters}..."
            )
            print(f"      Chunks {start_idx}-{end_idx} ({len(chapter_chunks)} chunks)")

            # Generate chapter title and summary using NeuralSeek make_chapter agent
            print(f"      🤖 Calling NeuralSeek make_chapter agent...")
            chapter_info = self._generate_chapter_summary(chapter_chunks[:5])
            print(f"      ✅ Got title: '{chapter_info['title']}'")

            # Use UUID objects, not strings, to match the model
            chapter_id = uuid.uuid4()
            chapter_number = len(chapters_data) + 1
            chapter_title = chapter_info["title"]
            chapter_summary = chapter_info["summary"]

            chapter_data = {
                "id": str(chapter_id),  # Store as string for JSON serialization
                "document_id": document_id,
                "chapter_number": chapter_number,
                "title": chapter_title,
                "summary": chapter_summary,
                "start_chunk_idx": start_idx,
                "end_chunk_idx": end_idx,
            }

            chapters_data.append(chapter_data)

            # Create Chapter record in database with UUID objects
            # Convert document_id to UUID if it's a string
            doc_uuid = (
                uuid.UUID(document_id) if isinstance(document_id, str) else document_id
            )

            chapter = Chapter(
                id=chapter_id,  # Pass UUID object, not string
                doc_id=doc_uuid,  # Pass UUID object, not string
                chapter_number=chapter_number,
                title=chapter_title,
                summary=chapter_summary,
            )
            self.db.add(chapter)

            print(f"   📖 Created '{chapter_title}': chunks {start_idx}-{end_idx}")
            print(f"      Summary: {chapter_summary[:100]}...")

        self.db.commit()
        print(f"✅ Created {len(chapters_data)} symbolic chapters")

        return chapters_data

    def _generate_chapter_summary(self, chapter_chunks: List[str]) -> Dict[str, str]:
        """
        Generate a title and summary for a chapter using NeuralSeek make_chapter agent.
        Falls back to a simple description if API fails.

        Args:
            chapter_chunks: First few chunks of the chapter

        Returns:
            Dict with 'title' and 'summary' keys
        """
        import asyncio

        try:
            # Import call_maistro_agent from utils
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils import call_maistro_agent

            # Combine first few chunks for context (limit to 3000 chars)
            chapter_text = "\n\n".join(chapter_chunks[:5])[:3000]

            # Call NeuralSeek make_chapter agent with timeout
            async def call_with_timeout():
                return await asyncio.wait_for(
                    call_maistro_agent(
                        agent_name="make_chapter", params={"chapter_text": chapter_text}
                    ),
                    timeout=30.0,  # 30 second timeout
                )

            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a new thread to run the coroutine
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, call_with_timeout())
                    response = future.result(
                        timeout=35.0
                    )  # 5 seconds extra for overhead
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                response = asyncio.run(call_with_timeout())

            print(f"      📥 Raw NeuralSeek response: {response}")

            # Parse the response
            answer = response.get("answer", "{}")
            print(f"      🔍 Answer field type: {type(answer)}")
            print(f"      🔍 Answer content: {answer}")

            # The answer might be a JSON string or already a dict
            if isinstance(answer, str):
                # Remove markdown code blocks if present
                if answer.startswith("```json"):
                    answer = answer.strip("```json").strip().strip("```")
                elif answer.startswith("```"):
                    answer = answer.strip("```").strip()

                import json

                chapter_data = json.loads(answer)
            elif isinstance(answer, dict):
                chapter_data = answer
            else:
                raise ValueError(f"Unexpected answer type: {type(answer)}")

            title = chapter_data.get("title", "Section")
            summary = chapter_data.get("summary", "")

            print(f"      ✅ Parsed title: '{title}'")
            print(f"      ✅ Parsed summary: '{summary[:100]}...'")

            return {
                "title": title[:200],  # Limit title length
                "summary": summary[:500],  # Limit summary length
            }

        except asyncio.TimeoutError:
            print(f"⚠️  Chapter summary generation timed out (30s) - using fallback")
            # Fallback: Return generic title and first 200 chars of first chunk
            return {
                "title": "Section",
                "summary": (
                    chapter_chunks[0][:200] + "..."
                    if chapter_chunks
                    else "Section content"
                ),
            }
        except Exception as e:
            print(f"⚠️  Chapter summary generation failed: {e}")

            # Fallback: Return generic title and first 200 chars of first chunk
            return {
                "title": "Section",
                "summary": (
                    chapter_chunks[0][:200] + "..."
                    if chapter_chunks
                    else "Section content"
                ),
            }

    def _index_chunks_with_chapters(
        self,
        document_id: str,
        chunks: List[str],
        document_name: str,
        chapters_data: List[Dict[str, Any]],
    ) -> int:
        """
        Index chunks with their assigned chapter IDs.

        Args:
            document_id: Document UUID
            chunks: All text chunks
            document_name: Name of document
            chapters_data: List of chapter metadata with start/end indices

        Returns:
            Number of indexed chunks
        """
        indexed_count = 0

        with self.indexer.driver.session() as session:
            # Create root Document node
            session.run(
                """
            MERGE (d:Document {id: $doc_id})
            SET d.name = $name, d.created_at = datetime()
            """,
                doc_id=document_id,
                name=document_name,
            )

            print(f"📚 Created Document node: {document_id}")

            # Index each chunk with its chapter_id
            for i, chunk_text in enumerate(chunks):
                try:
                    # Find which chapter this chunk belongs to
                    chapter_id = None
                    for chapter in chapters_data:
                        if chapter["start_chunk_idx"] <= i < chapter["end_chunk_idx"]:
                            chapter_id = chapter["id"]
                            break

                    # Progress indicator every 10 chunks
                    if (i + 1) % 10 == 0:
                        progress = ((i + 1) / len(chunks)) * 100
                        print(
                            f"   🔗 Indexing progress: {i + 1}/{len(chunks)} chunks ({progress:.1f}%)"
                        )

                    # Generate embedding
                    embedding = self.indexer.embedding_model.encode(chunk_text).tolist()

                    # Extract concepts (optional)
                    concepts = []
                    if self.indexer.extract_concepts_enabled:
                        concepts = self.indexer.concept_extractor.extract_concepts(
                            chunk_text
                        )

                    # Create Chunk node with chapter_id
                    session.run(
                        """
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
                        index=i,
                    )

                    # Link concepts
                    if concepts:
                        session.run(
                            """
                        MATCH (c:Chunk {document_id: $doc_id, chunk_index: $index})
                        WITH c
                        UNWIND $concepts AS concept_name
                        MERGE (con:Concept {name: concept_name})
                        CREATE (c)-[:MENTIONS]->(con)
                        """,
                            doc_id=document_id,
                            index=i,
                            concepts=concepts,
                        )

                    indexed_count += 1

                except Exception as e:
                    print(f"⚠️  Error indexing chunk {i}: {e}")
                    continue

        print(f"✅ Indexed {indexed_count} chunks with chapter assignments")
        return indexed_count

    def process_upload(
        self, pdf_bytes: bytes, filename: str, user_id: str, storage_url: str
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
            status="processing",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        print(f"📝 Created Document record: {doc.id}")

        try:
            # Phase 1.2: Chunk the PDF
            print(f"\n📄 Phase 1.2: Extracting and chunking PDF...")
            text = self.pdf_processor.extract_text_from_pdf(pdf_bytes)
            chunks = self.pdf_processor.chunk_text(text)

            print(f"✅ Chunking complete: {len(chunks)} chunks from PDF")

            # Phase 1.3: Create Symbolic Chapters
            print(f"\n📊 Phase 1.3: Creating symbolic chapters...")
            chapters_data = self._create_symbolic_chapters(chunks, str(doc.id))
            print(
                f"✅ Chapter creation complete: {len(chapters_data)} chapters created"
            )

            # Phase 1.4: Build the Graph + Vector Index with chapter assignments
            print(f"\n🔗 Phase 1.4: Indexing chunks in Neo4j...")
            indexed_count = self._index_chunks_with_chapters(
                document_id=str(doc.id),
                chunks=chunks,
                document_name=filename,
                chapters_data=chapters_data,
            )

            # Update status
            self.db.query(Document).filter(Document.id == doc.id).update(
                {"status": "ready"}
            )
            self.db.commit()
            self.db.refresh(doc)

            print(f"✅ Upload complete: {filename} ({indexed_count} chunks)")
            return doc

        except Exception as e:
            print(f"❌ Upload failed: {e}")
            # Rollback the transaction first to clear any errors
            self.db.rollback()

            # Then try to update the document status
            try:
                self.db.query(Document).filter(Document.id == doc.id).update(
                    {"status": "error"}
                )
                self.db.commit()
            except Exception as update_error:
                print(f"⚠️  Failed to update document status: {update_error}")
                self.db.rollback()

            raise

    def generate_question_from_document(
        self, document_id: str, topic: Optional[str] = None
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
            document_id=document_id, query_text=query, top_k=5
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
                model="gemini-2.0-flash-exp", contents=prompt
            )

            # Parse response (simplified - add proper JSON parsing)
            return {
                "document_id": document_id,
                "question": response.text,
                "context_chunks": len(relevant_chunks),
                "relevant_chunks": relevant_chunks,
            }

        except Exception as e:
            print(f"❌ Question generation failed: {e}")
            raise


# Convenience function for FastAPI route
def upload_pdf_to_graphrag(
    pdf_bytes: bytes, filename: str, user_id: str, storage_url: str, db_session: Session
) -> Document:
    """
    Convenience wrapper for upload pipeline
    Use this in your FastAPI /upload endpoint
    """
    pipeline = DocumentUploadPipeline(db_session)
    return pipeline.process_upload(pdf_bytes, filename, user_id, storage_url)
