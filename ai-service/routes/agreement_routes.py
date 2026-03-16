from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.config import get_settings, validate_api_key
from services.agreement_analysis_service import agreement_analysis_service
from utils.pdf_parser import extract_text_from_pdf_bytes, sanitize_text, validate_upload_size

router = APIRouter(prefix="/ai", tags=["agreement"], dependencies=[Depends(validate_api_key)])


@router.post("/analyze-agreement")
async def analyze_agreement(
    request: Request,
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    user_context: str | None = Form(default=None),
) -> dict:
    settings = get_settings()
    extracted_text = text or ""
    parsed_user_context: dict = {}

    if not extracted_text and file is None and request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json()
        extracted_text = str((body or {}).get("text") or "")
        raw_user_context = (body or {}).get("user_context") or (body or {}).get("userContext") or {}
        if isinstance(raw_user_context, dict):
            parsed_user_context = raw_user_context

    if user_context:
        try:
            candidate = json.loads(user_context)
            if isinstance(candidate, dict):
                parsed_user_context = candidate
        except json.JSONDecodeError:
            parsed_user_context = {}

    if file is not None:
        data = await file.read()
        size_error = validate_upload_size(data, settings.max_upload_mb)
        if size_error:
            raise HTTPException(status_code=413, detail=size_error)

        if file.filename and file.filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf_bytes(data)
        else:
            extracted_text = sanitize_text(data.decode("utf-8", errors="ignore"))

    extracted_text = sanitize_text(extracted_text)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No agreement text provided")

    analysis = agreement_analysis_service.analyze(extracted_text, user_context=parsed_user_context)
    return analysis