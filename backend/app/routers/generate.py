import io
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
import httpx
from google import genai
from google.genai import types as gen_types

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
SIZE_TO_COUNT = {"small": 25, "large": 50}


@router.post("/from-link")
async def generate_from_link(
    url: str = Form(...),
    size: str = Form("small"),
    topic: Optional[str] = Form(None),
    sub_topic: Optional[str] = Form(None),
):
    if not settings.get("GENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    client = genai.Client(api_key=settings["GENAI_API_KEY"])

    # Download the URL content and infer MIME type
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client_http:
            resp = await client_http.get(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="failed_to_fetch_url") from exc

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="bad_url_status")

    content_bytes = resp.content
    content_type_header = resp.headers.get("content-type", "").split(";")[0].lower()

    # Heuristics for MIME type
    mime_type = content_type_header or ""
    if not mime_type or mime_type == "application/octet-stream":
        if url.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        elif url.lower().endswith((".htm", ".html")):
            mime_type = "text/html"
        else:
            # default to text/html for typical web pages
            mime_type = "text/html"

    if mime_type not in ("application/pdf", "text/html", "text/plain"):
        raise HTTPException(status_code=400, detail="unsupported_content_type")

    # Upload to Files API
    uploaded = client.files.upload(
        file=io.BytesIO(content_bytes),
        config=dict(mime_type=mime_type),
    )

    count = SIZE_TO_COUNT.get(size.lower(), 25)
    prompt = (
    f"You are an expert learning coach specializing in cognitive science. Your task is to generate {count} "
    "high-efficacy multiple-choice questions (MCQs) from the provided text. The primary goal is to maximize "
    "long-term memory retention and deep conceptual understanding by actively forcing effortful retrieval and "
    "combating the forgetting curve."

    "**Core Directives:**"
    "1.  **Question Distribution (Target Mix):**"
    "    - **~30% Factual Recall:** Key definitions, facts, and critical data points."
    "    - **~40% Conceptual Understanding:** Questions that test the 'why' and 'how' behind the facts, requiring inference."
    "    - **~20% Application & Scenario-Based:** Place the user in a situation where they must apply the knowledge to solve a problem."
    "    - **~10% Integrative Thinking:** Questions that require connecting concepts from different sections of the document, fostering a holistic view (interleaving)."

    "2.  **Simulate Open-Ended Challenge:**"
    "    - Although the format is MCQ, the questions must demand deep processing. Frame them to simulate the cognitive load of open-ended questions. Use phrasing like: 'What is the primary reason for...?', 'Which of the following best explains the relationship between X and Y?', or 'How would Concept A affect Outcome B?'"

    "3.  **High-Effort Distractors:**"
    "    - Generate one unambiguously correct answer based *only* on the source text."
    "    - The three distractors must be highly plausible, targeting common misconceptions, subtle distinctions, or logically related but incorrect ideas. Avoid trivial or obviously wrong options. The user should have to pause and think critically."

    "4.  **Comprehensive & Non-Redundant Coverage:**"
    "    - Distribute questions proportionally across the document's main topics."
    "    - Ensure each question tests a unique concept or application to avoid trivial duplication."

    "5.  **Critical Explanation Field:**"
    "    - The 'explanation' is the most important part of the learning loop. It must be a concise micro-lesson."
    "    - **Core Principle:** Start by stating the key idea or principle the question is testing."
    "    - **Justify Correct Answer:** Briefly explain why the correct option is correct, citing the logic from the document."
    "    - **Deconstruct Distractors:** For each incorrect option, explain precisely *why* it is wrong. This is crucial for learning from errors."
    "    - **Memory Anchor:** Provide a short, memorable cue. This could be an analogy, a mnemonic, or a 'Connect this to...' tip that links the idea to another concept in the document, enhancing consolidation."

   
)
    response = client.models.generate_content(
        model=settings["GENAI_MODEL"],
        contents=[uploaded, prompt],
        config=gen_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MCQ_ARRAY_SCHEMA,
        ),
    )
    return await _persist_generated_questions(topic or None, sub_topic or None, response.text, count, unify_topic=True)


@router.post("/from-pdf")
async def generate_from_pdf(
    pdf: UploadFile = File(...),
    size: str = Form("small"),
    topic: Optional[str] = Form(None),
    sub_topic: Optional[str] = Form(None),
):
    if not settings.get("GENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="genai_api_key_missing")
    content = await pdf.read()
    client = genai.Client(api_key=settings["GENAI_API_KEY"])

    count = SIZE_TO_COUNT.get(size.lower(), 25)
    prompt = (
    f"You are an expert learning coach specializing in cognitive science. Your task is to generate {count} "
    "high-efficacy multiple-choice questions (MCQs) from the provided text. The primary goal is to maximize "
    "long-term memory retention and deep conceptual understanding by actively forcing effortful retrieval and "
    "combating the forgetting curve."

    "**Core Directives:**"
    "1.  **Question Distribution (Target Mix):**"
    "    - **~30% Factual Recall:** Key definitions, facts, and critical data points."
    "    - **~40% Conceptual Understanding:** Questions that test the 'why' and 'how' behind the facts, requiring inference."
    "    - **~20% Application & Scenario-Based:** Place the user in a situation where they must apply the knowledge to solve a problem."
    "    - **~10% Integrative Thinking:** Questions that require connecting concepts from different sections of the document, fostering a holistic view (interleaving)."

    "2.  **Simulate Open-Ended Challenge:**"
    "    - Although the format is MCQ, the questions must demand deep processing. Frame them to simulate the cognitive load of open-ended questions. Use phrasing like: 'What is the primary reason for...?', 'Which of the following best explains the relationship between X and Y?', or 'How would Concept A affect Outcome B?'"

    "3.  **High-Effort Distractors:**"
    "    - Generate one unambiguously correct answer based *only* on the source text."
    "    - The three distractors must be highly plausible, targeting common misconceptions, subtle distinctions, or logically related but incorrect ideas. Avoid trivial or obviously wrong options. The user should have to pause and think critically."

    "4.  **Comprehensive & Non-Redundant Coverage:**"
    "    - Distribute questions proportionally across the document's main topics."
    "    - Ensure each question tests a unique concept or application to avoid trivial duplication."

    "5.  **Critical Explanation Field:**"
    "    - The 'explanation' is the most important part of the learning loop. It must be a concise micro-lesson."
    "    - **Core Principle:** Start by stating the key idea or principle the question is testing."
    "    - **Justify Correct Answer:** Briefly explain why the correct option is correct, citing the logic from the document."
    "    - **Deconstruct Distractors:** For each incorrect option, explain precisely *why* it is wrong. This is crucial for learning from errors."
    "    - **Memory Anchor:** Provide a short, memorable cue. This could be an analogy, a mnemonic, or a 'Connect this to...' tip that links the idea to another concept in the document, enhancing consolidation."

   
)
    # Upload PDF to Files API and generate with strict JSON schema
    uploaded = client.files.upload(
        file=io.BytesIO(content),
        config=dict(mime_type="application/pdf"),
    )
    response = client.models.generate_content(
        model=settings["GENAI_MODEL"],
        contents=[uploaded, prompt],
        config=gen_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MCQ_ARRAY_SCHEMA,
        ),
    )
    return await _persist_generated_questions(topic or None, sub_topic or None, response.text, count, unify_topic=True)


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
        use_sub_topic = (item.get("sub_topic") or sub_topic_name or "Misc")

        topic_id = await db.fetchval(
            "INSERT INTO topics(name) VALUES($1) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            use_topic.strip(),
        )
        sub_topic_id = await db.fetchval(
            """
            INSERT INTO sub_topics(topic_id, name)
            VALUES($1, $2)
            ON CONFLICT (topic_id, name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            topic_id,
            use_sub_topic.strip(),
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


