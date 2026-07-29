# API Reference Guide

> **Document:** API_REFERENCE.md
> **Version:** 1.0.0
> **Target Audience:** React Frontend Developers
> **Last Updated:** 2026-07-28

This document serves as the formal API contract for the Hybrid GraphRAG Backend (Phase 8.5). All endpoints are prefixed with `/api/v1`.

---

## 1. Authentication
Authentication is handled via Supabase JWTs. All protected endpoints expect a valid JWT in the `Authorization` header.

**Header Format:**
```
Authorization: Bearer <Supabase_JWT>
```

---

## 2. User Endpoints

### 2.1 Get Current User Profile
**Purpose:** Fetch profile information for the authenticated user.
- **HTTP Method:** `GET`
- **Route:** `/api/v1/users/me`
- **Authentication Required:** Yes
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:** None
- **Response Body:**
  ```json
  {
    "id": "uuid",
    "supabase_user_id": "string",
    "email": "string",
    "username": "string",
    "role": "USER",
    "is_active": true,
    "authenticated": true,
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
  ```
- **Status Codes:** `200 OK`, `401 Unauthorized`

---

## 3. Document Endpoints

### 3.1 Upload Document
**Purpose:** Upload a PDF, DOCX, or TXT file for processing.
- **HTTP Method:** `POST`
- **Route:** `/api/v1/documents/upload`
- **Authentication Required:** Yes
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
- **Multipart Uploads:** 
  - `file`: The binary file being uploaded.
- **Response Body:**
  ```json
  {
    "id": "uuid",
    "filename": "document.pdf",
    "status": "UPLOADED",
    "message": "Upload successful, processing started."
  }
  ```
- **Status Codes:** `201 Created`, `400 Bad Request`, `413 Payload Too Large`

### 3.2 List Documents
**Purpose:** Fetch all documents owned by the authenticated user.
- **HTTP Method:** `GET`
- **Route:** `/api/v1/documents`
- **Authentication Required:** Yes
- **Response Body:**
  ```json
  [
    {
      "id": "uuid",
      "filename": "string",
      "status": "COMPLETED",
      "file_size": 1048576,
      "created_at": "timestamp"
    }
  ]
  ```

### 3.3 Get Document Status
**Purpose:** Fetch the detailed processing status of a single document.
- **HTTP Method:** `GET`
- **Route:** `/api/v1/documents/{document_id}`
- **Authentication Required:** Yes
- **Response Body:**
  ```json
  {
    "id": "uuid",
    "filename": "string",
    "status": "COMPLETED",
    "vector_status": "EMBEDDED",
    "entity_extraction_status": "COMPLETED",
    "chunk_count": 42
  }
  ```

### 3.4 Delete Document
**Purpose:** Delete a document and its associated vectors/entities.
- **HTTP Method:** `DELETE`
- **Route:** `/api/v1/documents/{document_id}`
- **Authentication Required:** Yes
- **Response Body:** `204 No Content`

---

## 4. Chat Endpoints

### 4.1 Hybrid GraphRAG Query
**Purpose:** Ask a question over the knowledge base (uses Hybrid Vector + Graph search).
- **HTTP Method:** `POST`
- **Route:** `/api/v1/chat/query`
- **Authentication Required:** Yes
- **Request Body:**
  ```json
  {
    "query": "What is the hybrid architecture?",
    "conversation_id": "uuid (optional)"
  }
  ```
- **Response Body:**
  ```json
  {
    "answer": "The hybrid architecture combines Qdrant and Neo4j...",
    "sources": [
      {
        "document_id": "uuid",
        "score": 0.89,
        "content": "...",
        "page_number": 4
      }
    ],
    "entities": [
      {
        "name": "Qdrant",
        "type": "Database"
      }
    ]
  }
  ```
- **Status Codes:** `200 OK`, `400 Bad Request`

### 4.2 Voice Query (End-to-End Voice Chat)
**Purpose:** Speak a question and receive an audio response. Uses Whisper STT, Language Detection, GraphRAG, and Orpheus TTS.
- **HTTP Method:** `POST`
- **Route:** `/api/v1/chat/voice-query`
- **Authentication Required:** Yes
- **Headers:** `Content-Type: multipart/form-data`
- **Multipart Uploads:** 
  - `audio_file`: The user's audio input (WAV/WebM).
- **Response Body:**
  ```json
  {
    "transcription": "What is the hybrid architecture?",
    "detected_language": "en",
    "answer": "The hybrid architecture combines...",
    "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
    "sources": [...]
  }
  ```
- **Status Codes:** `200 OK`, `400 Bad Request`, `500 Internal Server Error`

---

## 5. Audio Utilities (Optional / Debug)

### 5.1 Transcribe Audio
**Purpose:** Standalone Speech-to-Text utility.
- **HTTP Method:** `POST`
- **Route:** `/api/v1/audio/transcribe`
- **Authentication Required:** Yes
- **Request:** `multipart/form-data` -> `file`
- **Response:** `{ "text": "...", "language": "en" }`

### 5.2 Synthesize Speech
**Purpose:** Standalone Text-to-Speech utility.
- **HTTP Method:** `POST`
- **Route:** `/api/v1/audio/synthesize`
- **Authentication Required:** Yes
- **Request:** `{ "text": "Hello world", "language": "en" }`
- **Response:** Returns raw audio stream (`audio/mpeg`).
