import io
import random
from typing import List, Optional, cast, Any

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
import httpx
from google import genai
from google.genai import types as gen_types
from google.genai.errors import ServerError

from ..config import load_settings
from ..db import db


router = APIRouter(prefix="/generate", tags=["generate"])
settings = load_settings()

# JSON schema for an array of MCQs
MCQ_ARRAY_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "required": ["question_text", "choices", "correct_index"],
        "properties": {
            "question_text": {"type": "STRING"},
            "explanation": {"type": "STRING"},
            "image_url": {"type": "STRING"},
            "choices": {"type": "ARRAY", "items": {"type": "STRING"}},
            "correct_index": {"type": "INTEGER"},
            "topic": {"type": "STRING"},
            "sub_topic": {"type": "STRING"},
        },
    },
}

# Map requested size to a question count
SIZE_TO_COUNT = {"tiny": 5, "small": 25, "large": 50}

# Recognized YouTube hosts for special handling via file_uri
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}


def build_generation_prompt(count: int) -> str:
    # Centralized prompt used across all generation flows
    return (
        f"You are an expert learning coach specializing in cognitive science. Your task is to generate {count} "
        "high-efficacy multiple-choice questions (MCQs) from the provided text. The primary goal is to maximize "
        "long-term memory retention and deep conceptual understanding by actively forcing effortful retrieval and "
        "combating the forgetting curve."

        "\n\n**CRITICAL: CONTEXT-FREE DESIGN PRINCIPLE:**"
        "\n- These questions will be reviewed MONTHS after reading, when the user has completely forgotten the source article."
        "\n- Every question MUST be fully self-contained with all necessary context embedded directly in the question stem."
        "\n- Extract the GENERAL PRINCIPLE or CONCEPT from the article and test that, not the article's specific example or narrative."
        "\n- Transform article-specific scenarios into universal, timeless knowledge questions."
        "\n- NEVER reference: 'the article', 'the author', 'the text', 'the study mentioned', 'the experiment described', or any meta-references to the source."

        "\n\n**Core Directives:**"
        "\n1.  **Question Distribution (Target Mix):**"
        "\n    - **~30% Factual Recall:** Key definitions, facts, and critical data points (presented as general knowledge)."
        "\n    - **~40% Conceptual Understanding:** Questions that test the 'why' and 'how' behind principles, requiring inference."
        "\n    - **~20% Application & Scenario-Based:** Create NEW hypothetical scenarios that test the same principle from the article."
        "\n    - **~10% Integrative Thinking:** Questions that require connecting concepts, fostering a holistic view."

        "\n2.  **Transform Article Content into Universal Questions:**"
        "\n    - **Instead of:** 'The author's experiment using AI image generation showed...'"
        "\n    - **Write:** 'In AI image generation systems, when training data contains biased representations, what is the most likely outcome?'"
        "\n    "
        "\n    - **Instead of:** 'According to the article, what trend was observed?'"
        "\n    - **Write:** 'What psychological principle explains why AI-generated images of people tend toward conventionally attractive features?'"
        "\n    "
        "\n    - **Key technique:** Identify the underlying principle, theory, or mechanism in the article, then ask about THAT directly."

        "\n3.  **Embed All Necessary Context in the Question:**"
        "\n    - If the article discusses a specific case, extract the generalizable lesson and include enough context for the question to make sense standalone."
        "\n    - Example: If an article discusses 'a 2023 study on neural networks,' your question should be: 'When neural networks are trained on imbalanced datasets, which of the following is most likely to occur?'"

        "\n4.  **Simulate Open-Ended Challenge:**"
        "\n    - Frame questions to demand deep processing: 'What is the primary mechanism by which...?', 'Which factor most significantly influences...?', 'In a scenario where X occurs, what would be the most likely outcome for Y?'"

        "\n5.  **High-Effort Distractors:**"
        "\n    - Generate one unambiguously correct answer based on the concepts from the source text."
        "\n    - Three distractors must be highly plausible, targeting common misconceptions or logically related but incorrect ideas."

        "\n6.  **Comprehensive & Non-Redundant Coverage:**"
        "\n    - Distribute questions proportionally across the document's main concepts."
        "\n    - Ensure each question tests a unique principle or application."

        "\n7.  **Critical Explanation Field:**"
        "\n    - **Core Principle:** Start by stating the general principle or concept being tested (NOT 'the article discusses')."
        "\n    - **Justify Correct Answer:** Explain why it's correct using conceptual reasoning, not article citations."
        "\n    - **Deconstruct Distractors:** For each incorrect option, explain precisely why it's wrong."
        "\n    - **Memory Anchor:** Provide a memorable analogy, mnemonic, or connection to related concepts."
        "\n    - **Maintain Context Independence:** The explanation should also be self-contained and never reference the source material."

        "\n\n**EXAMPLES OF TRANSFORMATION:**"
        "\n"
        "\n**BAD (Article-dependent):**"
        "\n'The author's experiment using facial recognition AI demonstrated what primary bias?'"
        "\n"
        "\n**GOOD (Self-contained, concept-based):**"
        "\n'When facial recognition systems are trained predominantly on datasets from Western countries, what type of bias is most commonly observed?'"
        "\n"
        "\n**BAD (Article-dependent):**"
        "\n'According to the article, what trend exacerbates AI-generated attractiveness?'"
        "\n"
        "\n**GOOD (Self-contained, concept-based):**"
        "\n'In machine learning systems that generate human faces, what phenomenon causes the outputs to converge toward conventionally attractive features over successive training iterations?'"
        "\n"
        "\n**OUTPUT FORMAT:**"
        "\nReturn a JSON array where each question object has:"
        "\n- 'question': The question text (fully self-contained)"
        "\n- 'options': Array of 4 options (A, B, C, D)"
        "\n- 'correct_answer': The letter of the correct option"
        "\n- 'explanation': Comprehensive explanation with principle, correct answer justification, distractor analysis, and memory anchor"
        "\n- 'difficulty': 'recall', 'conceptual', 'application', or 'integrative'"
    )


def detect_youtube(url: str) -> bool:
    # Identify if the URL points to YouTube; used to bypass fetching and use file_uri
    try:
        from urllib.parse import urlparse
    except Exception:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(h in host for h in YOUTUBE_HOSTS)


def _infer_mime_type(url: str, content_type_header: str) -> str:
    # Heuristics for MIME type for non-YouTube URLs
    mime_type = (content_type_header or "").split(";")[0].lower()
    if not mime_type or mime_type == "application/octet-stream":
        lower_url = url.lower()
        if lower_url.endswith(".pdf"):
            return "application/pdf"
        if lower_url.endswith((".htm", ".html")):
            return "text/html"
        return "text/html"
    return mime_type


async def create_content_part_for_url(client: genai.Client, url: str):
    # For YouTube, reference via file_uri part; otherwise fetch bytes and upload
    if detect_youtube(url):
        return gen_types.Part(file_data=gen_types.FileData(file_uri=url))

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client_http:
            resp = await client_http.get(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="failed_to_fetch_url") from exc

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="bad_url_status")

    content_bytes = resp.content
    mime_type = _infer_mime_type(url, resp.headers.get("content-type", ""))
    if mime_type not in ("application/pdf", "text/html", "text/plain"):
        raise HTTPException(status_code=400, detail="unsupported_content_type")

    uploaded: gen_types.File = client.files.upload(
        file=io.BytesIO(content_bytes),
        config=dict(mime_type=mime_type),
    )
    return uploaded


def _choose_api_key(keys: List[str]) -> str:
    # Prefer list of keys; fallback to single env if list is empty
    if keys:
        return random.choice(keys)
    return settings.get("GENAI_API_KEY", "")


def _generate_with_fallback(
    client: genai.Client,
    uploaded: gen_types.File,
    prompt: str,
    model_primary: str,
    model_secondary: str,
):
    try:
        return client.models.generate_content(
            model=model_primary,
            contents=cast(Any, [uploaded, prompt]),
            config=gen_types.GenerateContentConfig(
                thinking_config=gen_types.ThinkingConfig(
                    thinking_budget=128,
                ),
                response_mime_type="application/json",
                response_schema=MCQ_ARRAY_SCHEMA,
            ),
        )
    except ServerError as exc:
        # Only fallback on overload/unavailable
        status_text = str(exc)
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        is_overloaded = (code == 503) or ("UNAVAILABLE" in status_text)
        if not is_overloaded:
            raise
        # Fallback attempt
        return client.models.generate_content(
            model=model_secondary,
            contents=cast(Any, [uploaded, prompt]),
            config=gen_types.GenerateContentConfig(
                thinking_config=gen_types.ThinkingConfig(
                    thinking_budget=0,
                ),
                response_mime_type="application/json",
                response_schema=MCQ_ARRAY_SCHEMA,
            ),
        )


def _generate_with_fallback_parts(
    client: genai.Client,
    parts: List[Any],
    model_primary: str,
    model_secondary: str,
):
    try:
        return client.models.generate_content(
            model=model_primary,
            contents=cast(Any, parts),
            config=gen_types.GenerateContentConfig(
                thinking_config=gen_types.ThinkingConfig(
                    thinking_budget=128,
                ),
                response_mime_type="application/json",
                response_schema=MCQ_ARRAY_SCHEMA,
            ),
        )
    except ServerError as exc:
        status_text = str(exc)
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        is_overloaded = (code == 503) or ("UNAVAILABLE" in status_text)
        if not is_overloaded:
            raise
        return client.models.generate_content(
            model=model_secondary,
            contents=cast(Any, parts),
            config=gen_types.GenerateContentConfig(
                thinking_config=gen_types.ThinkingConfig(
                    thinking_budget=0,
                ),
                response_mime_type="application/json",
                response_schema=MCQ_ARRAY_SCHEMA,
            ),
        )


@router.post("/from-link")
async def generate_from_link(
    url: str = Form(...),
    size: str = Form("small"),
    topic: Optional[str] = Form(None),
    sub_topic: Optional[str] = Form(None),
):
    # Ensure we have at least one key
    if not settings.get("GENAI_API_KEYS") and not settings.get("GENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    api_key = _choose_api_key(settings.get("GENAI_API_KEYS", []))
    if not api_key:
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    client = genai.Client(api_key=api_key)

    count = SIZE_TO_COUNT.get(size.lower(), 25)
    prompt = build_generation_prompt(count)

    part_or_file = await create_content_part_for_url(client, url)
    response = _generate_with_fallback_parts(
        client=client,
        parts=[part_or_file, prompt],
        model_primary=settings.get("GEN_AI_MODEL_1", settings.get("GENAI_MODEL")),
        model_secondary=settings.get("GEN_AI_MODEL_2", settings.get("GENAI_MODEL")),
    )
    response_text: str = response.text or "[]"
    return await _persist_generated_questions(topic or None, sub_topic or None, response_text, count, unify_topic=True)


@router.post("/from-pdf")
async def generate_from_pdf(
    pdf: UploadFile = File(...),
    size: str = Form("small"),
    topic: Optional[str] = Form(None),
    sub_topic: Optional[str] = Form(None),
):
    if not settings.get("GENAI_API_KEYS") and not settings.get("GENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    content = await pdf.read()
    api_key = _choose_api_key(settings.get("GENAI_API_KEYS", []))
    if not api_key:
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    client = genai.Client(api_key=api_key)

    count = SIZE_TO_COUNT.get(size.lower(), 25)
    prompt = build_generation_prompt(count)
    # Upload PDF to Files API and generate with strict JSON schema
    uploaded: gen_types.File = client.files.upload(
        file=io.BytesIO(content),
        config=dict(mime_type="application/pdf"),
    )
    response = _generate_with_fallback(
        client=client,
        uploaded=uploaded,
        prompt=prompt,
        model_primary=settings.get("GEN_AI_MODEL_1", settings.get("GENAI_MODEL")),
        model_secondary=settings.get("GEN_AI_MODEL_2", settings.get("GENAI_MODEL")),
    )
    response_text: str = response.text or "[]"
    return await _persist_generated_questions(topic or None, sub_topic or None, response_text, count, unify_topic=True)


@router.post("/from-links")
async def generate_from_links(
    urls: List[str] = Form(...),
    size: str = Form("small"),
    topic: Optional[str] = Form(None),
    sub_topic: Optional[str] = Form(None),
):
    if not settings.get("GENAI_API_KEYS") and not settings.get("GENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    api_key = _choose_api_key(settings.get("GENAI_API_KEYS", []))
    if not api_key:
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    client = genai.Client(api_key=api_key)

    # Clean and validate URLs
    normalized_urls: List[str] = [u.strip() for u in urls if (u or "").strip()]
    if not normalized_urls:
        raise HTTPException(status_code=400, detail="no_urls_provided")
    if len(normalized_urls) > 5:
        raise HTTPException(status_code=400, detail="too_many_links")

    count = SIZE_TO_COUNT.get(size.lower(), 25)
    prompt = build_generation_prompt(count)

    parts: List[Any] = []
    for u in normalized_urls:
        part_or_file = await create_content_part_for_url(client, u)
        parts.append(part_or_file)
    parts.append(prompt)

    response = _generate_with_fallback_parts(
        client=client,
        parts=parts,
        model_primary=settings.get("GEN_AI_MODEL_1", settings.get("GENAI_MODEL")),
        model_secondary=settings.get("GEN_AI_MODEL_2", settings.get("GENAI_MODEL")),
    )
    response_text: str = response.text or "[]"
    return await _persist_generated_questions(topic or None, sub_topic or None, response_text, count, unify_topic=True)


@router.post("/from-text")
async def generate_from_text(
    text: str = Form(...),
    size: str = Form("small"),
    topic: Optional[str] = Form(None),
    sub_topic: Optional[str] = Form(None),
):
    if not settings.get("GENAI_API_KEYS") and not settings.get("GENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    api_key = _choose_api_key(settings.get("GENAI_API_KEYS", []))
    if not api_key:
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    client = genai.Client(api_key=api_key)

    source_text = (text or "").strip()
    if not source_text:
        raise HTTPException(status_code=400, detail="empty_text")

    count = SIZE_TO_COUNT.get(size.lower(), 25)
    prompt = build_generation_prompt(count)

    parts: List[Any] = [gen_types.Part(text=source_text), prompt]
    response = _generate_with_fallback_parts(
        client=client,
        parts=parts,
        model_primary=settings.get("GEN_AI_MODEL_1", settings.get("GENAI_MODEL")),
        model_secondary=settings.get("GEN_AI_MODEL_2", settings.get("GENAI_MODEL")),
    )
    response_text: str = response.text or "[]"
    return await _persist_generated_questions(topic or None, sub_topic or None, response_text, count, unify_topic=True)


async def _persist_generated_questions(topic_name: Optional[str], sub_topic_name: Optional[str], json_text: str, requested_count: int, unify_topic: bool = True):
    import json

    # Parse and normalize data
    parsed = json.loads(json_text)
    if not isinstance(parsed, list):
        # If the model returns a single object, wrap it
        data = [parsed]
    else:
        data = parsed

    # Enforce count exactly
    count = max(0, int(requested_count or 0))
    if count > 0:
        data = data[:count]

    # Determine a single topic for the whole document if requested
    document_topic = (topic_name or None)
    if unify_topic:
        if not document_topic:
            # Pick first non-empty item topic if present, else default
            for it in data:
                candidate = (it.get("topic") or "").strip()
                if candidate:
                    document_topic = candidate
                    break
        if not document_topic:
            document_topic = "General"

    created = 0
    for item in data:
        use_topic = document_topic if unify_topic else (item.get("topic") or topic_name or "General")
        # If the user supplied a sub_topic, always use it for all questions.
        # If only a topic was supplied, let the model's per-item sub_topic be used.
        use_sub_topic = (sub_topic_name or item.get("sub_topic") or "Misc")

        topic_id = await db.fetchval(
            "INSERT INTO topics(name) VALUES($1) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            str(use_topic).strip(),
        )
        sub_topic_id = await db.fetchval(
            """
            INSERT INTO sub_topics(topic_id, name)
            VALUES($1, $2)
            ON CONFLICT (topic_id, name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            topic_id,
            str(use_sub_topic).strip(),
        )
        qid = await db.fetchval(
            """
            INSERT INTO questions(sub_topic_id, question_text, explanation, image_url)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            sub_topic_id,
            item.get("question_text"),
            item.get("explanation"),
            item.get("image_url"),
        )
        options: List[str] = item.get("choices", [])
        correct_index = int(item.get("correct_index", 0))
        for idx, text in enumerate(options):
            await db.execute(
                """
                INSERT INTO choices(question_id, choice_text, is_correct)
                VALUES ($1, $2, $3)
                """,
                qid,
                text,
                idx == correct_index,
            )
        created += 1

    return {"status": "ok", "requested": requested_count, "created": created, "topic": document_topic or topic_name or "General"}


