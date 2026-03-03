"""Grounded answerer implementation using LLM.

This module provides an LLM-based answer generator that:
- Grounds answers in retrieved context only
- Cites sources via email_hash references
- Constrains inference to retrieved items only
"""

import logging
from typing import Any

from pydantic import BaseModel

from src.llm.answering import AnswerGenerationError
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


class GroundedAnswerResponse(BaseModel):
    """Structured response for grounded answering."""

    answer: str
    citations: list[str]


GROUNDED_ANSWER_SYSTEM_PROMPT = """You are an insurance claims assistant. Your role is to answer questions based ONLY on the provided context.

IMPORTANT RULES:
1. ONLY use information from the provided context documents
2. If the context doesn't contain enough information to answer the question, say so explicitly
3. ALWAYS cite your sources using the email_hash identifiers provided in the context
4. NEVER make up information or infer details not present in the context
5. Use a professional, concise tone appropriate for insurance operations

When citing sources, use the format: [email_hash:XXX] where XXX is the email hash from the context.

If you cannot find sufficient evidence in the context, respond with: "No evidence found in the available documents to answer this question."
"""


GROUNDED_ANSWER_USER_PROMPT = """Context (retrieved documents):

{context}

---

Question: {question}

Instructions:
1. Answer the question using ONLY the context above
2. If the context doesn't contain the answer, say so
3. Cite all sources using [email_hash:XXX] format
4. Keep your answer concise and professional
"""


class GroundedAnswerer:
    """LLM-based grounded answer generator.

    Generates answers that are constrained to retrieved context only.
    All answers cite sources via email_hash references.

    Usage:
        answerer = GroundedAnswerer(llm_client=OpenAIClient(...))
        result = await answerer.generate_answer(
            question="What are the high priority claims?",
            context=retrieved_context,
            citations=["hash1", "hash2"]
        )
    """

    def __init__(
        self,
        llm_client: LLMClient,
        temperature: float = 0.0,
    ):
        """Initialize the grounded answerer.

        Args:
            llm_client: LLM client for answer generation
            temperature: Temperature setting for generation
        """
        self._llm_client = llm_client
        self._temperature = temperature

    async def generate_answer(
        self,
        question: str,
        context: str,
        citations: list[str],
    ) -> dict[str, Any]:
        """Generate an answer grounded in the provided context.

        Args:
            question: User question
            context: Retrieved context from vector store
            citations: List of email_hash references

        Returns:
            Dictionary with answer, citations, and model info

        Raises:
            AnswerGenerationError: If answer generation fails
            CitationError: If citation validation fails
        """
        if not context or not citations:
            logger.warning(
                "No context or citations provided",
                extra={
                    "context_length": len(context),
                    "citations_count": len(citations),
                },
            )
            return {
                "answer": "No evidence found in the available documents to answer this question.",
                "citations": [],
                "model_name": self._llm_client.model_name,
            }

        user_prompt = GROUNDED_ANSWER_USER_PROMPT.format(
            context=context,
            question=question,
        )

        try:
            answer = await self._llm_client.generate(
                prompt=user_prompt,
                system_prompt=GROUNDED_ANSWER_SYSTEM_PROMPT,
                temperature=self._temperature,
            )

            if isinstance(answer, str):
                answer_text = answer
            elif isinstance(answer, dict):
                answer_text = answer.get("answer", answer)
            else:
                answer_text = str(answer)

            validated_citations = self._validate_citations(answer_text, citations)

            logger.info(
                "Answer generated",
                extra={
                    "question_length": len(question),
                    "answer_length": len(answer_text),
                    "citations_count": len(validated_citations),
                },
            )

            return {
                "answer": answer_text,
                "citations": validated_citations,
                "model_name": self._llm_client.model_name,
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise AnswerGenerationError(f"Failed to generate answer: {e}") from e

    def _validate_citations(
        self,
        answer: str,
        expected_citations: list[str],
    ) -> list[str]:
        """Validate that answer contains expected citations.

        Args:
            answer: Generated answer text
            expected_citations: List of expected email_hash values

        Returns:
            List of found citations
        """
        found_citations = []

        for citation in expected_citations:
            if citation in answer:
                found_citations.append(citation)

        if not found_citations and expected_citations:
            logger.warning(
                "No citations found in answer",
                extra={
                    "expected": expected_citations,
                    "answer_preview": answer[:200],
                },
            )

        return found_citations
