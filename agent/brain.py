"""
Survival Brain - Core AI logic for survival assistant.
Handles LLM interactions, knowledge retrieval, and message routing.
"""

import logging
import sys
import json
import requests
from typing import Generator, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from config.config import (
    OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    LLM_NUM_CTX, LLM_TIMEOUT, SYSTEM_PROMPT, KNOWLEDGE_BASE_DIR,
    KNOWLEDGE_TOP_K, RAG_ENABLED
)

logger = logging.getLogger(__name__)


class SurvivalBrain:
    """Core survival AI brain with RAG capabilities."""

    def __init__(self):
        self.ollama_url = OLLAMA_BASE_URL
        self.model = LLM_MODEL
        self.conversation_history = []
        self._rag_client = None
        self._knowledge_loaded = False

        # Initialize RAG if enabled
        if RAG_ENABLED:
            self._init_rag()

    def _init_rag(self):
        """Initialize ChromaDB for knowledge retrieval."""
        try:
            self._rag_client = chromadb.Client(ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            ))
            # Try to load existing collection or create new
            try:
                self.collection = self._rag_client.get_collection("survival_knowledge")
                logger.info("Loaded existing knowledge base")
            except:
                self.collection = self._rag_client.create_collection(
                    "survival_knowledge",
                    get_or_create=True
                )
                logger.info("Created new knowledge base")

            # Check if we have documents
            count = self.collection.count()
            if count > 0:
                self._knowledge_loaded = True
                logger.info(f"Knowledge base has {count} documents")
            else:
                # Load knowledge from files
                self._load_knowledge_files()
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}")
            self._rag_client = None

    def _load_knowledge_files(self):
        """Load markdown files into knowledge base."""
        if not KNOWLEDGE_BASE_DIR.exists():
            logger.warning(f"Knowledge base dir not found: {KNOWLEDGE_BASE_DIR}")
            return

        docs = []
        ids = []
        metadatas = []

        for md_file in KNOWLEDGE_BASE_DIR.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                doc_id = md_file.stem

                docs.append(content)
                ids.append(doc_id)
                metadatas.append({
                    "source": str(md_file.name),
                    "type": "survival_guide"
                })
                logger.info(f"Loaded: {md_file.name}")
            except Exception as e:
                logger.error(f"Failed to load {md_file}: {e}")

        if docs:
            try:
                self.collection.add(documents=docs, ids=ids, metadatas=metadatas)
                self._knowledge_loaded = True
                logger.info(f"Indexed {len(docs)} knowledge documents")
            except Exception as e:
                logger.error(f"Failed to index documents: {e}")

    def _retrieve_knowledge(self, query: str) -> list[str]:
        """Retrieve relevant knowledge for query."""
        if not self._rag_client or not self._knowledge_loaded:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=KNOWLEDGE_TOP_K
            )
            return results.get('documents', [[]])[0]
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")
            return []

    def check_systems(self) -> dict:
        """Check all system components."""
        status = {}

        # Check Ollama
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            status["ollama"] = "connected" if r.status_code == 200 else "error"
        except:
            status["ollama"] = "unavailable"

        # Check model loaded
        if status.get("ollama") == "connected":
            try:
                r = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model, "prompt": "test", "stream": False},
                    timeout=30
                )
                status["model"] = "loaded" if r.status_code == 200 else "error"
            except:
                status["model"] = "not_loaded"
        else:
            status["model"] = "unavailable"

        # Check knowledge base
        status["knowledge_base"] = "ready" if self._knowledge_loaded else "empty"

        return status

    def process(self, user_input: str, stream: bool = False, face_emotion: Optional[str] = None) -> str | Generator[str, None, None]:
        """Process user input and generate response."""
        # Retrieve relevant knowledge
        context_docs = self._retrieve_knowledge(user_input)
        context_str = "\n\n---\n\n".join(context_docs) if context_docs else ""

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add context if found
        if context_str:
            messages.append({
                "role": "system",
                "content": f"Relevant knowledge:\n{context_str}"
            })

        # Add conversation history
        for msg in self.conversation_history[-5:]:
            messages.append(msg)

        # Add current input
        messages.append({"role": "user", "content": user_input})

        # Build prompt for Ollama
        prompt = self._build_prompt(messages)

        if stream:
            return self._stream_response(prompt)
        else:
            return self._generate(prompt)

    def _build_prompt(self, messages: list) -> str:
        """Build prompt from messages for Ollama."""
        # Convert messages to chat format
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"{role.upper()}: {content}\n"
        prompt += "ASSISTANT: "
        return prompt

    def _generate(self, prompt: str) -> str:
        """Generate response from Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": LLM_TEMPERATURE,
                        "num_predict": LLM_MAX_TOKENS,
                        "num_ctx": LLM_NUM_CTX,
                    }
                },
                timeout=LLM_TIMEOUT
            )
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()

                # Add to history
                self.conversation_history.append({"role": "user", "content": prompt.split("USER: ")[-1].split("ASSISTANT:")[0] if "USER:" in prompt else prompt})
                self.conversation_history.append({"role": "assistant", "content": response_text})

                return response_text
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return "Error: Unable to generate response. Check Ollama connection."
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error: {str(e)}"

    def _stream_response(self, prompt: str) -> Generator[str, None, None]:
        """Stream response from Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": LLM_TEMPERATURE,
                        "num_predict": LLM_MAX_TOKENS,
                        "num_ctx": LLM_NUM_CTX,
                    }
                },
                timeout=LLM_TIMEOUT,
                stream=True
            )

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full_response += token
                        yield token
                    except:
                        continue

            # Add to history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            logger.error(f"Stream failed: {e}")
            yield f"Error: {str(e)}"

    def get_sources(self, query: str) -> list[dict]:
        """Get source documents for a query."""
        if not self._rag_client or not self._knowledge_loaded:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=KNOWLEDGE_TOP_K
            )
            sources = []
            for i, doc in enumerate(results.get('documents', [[]])[0]):
                meta = results.get('metadatas', [{}])[0][i] if results.get('metadatas') else {}
                sources.append({
                    "content": doc[:200] + "..." if len(doc) > 200 else doc,
                    "source": meta.get("source", "Unknown")
                })
            return sources
        except Exception as e:
            logger.warning(f"Source retrieval failed: {e}")
            return []