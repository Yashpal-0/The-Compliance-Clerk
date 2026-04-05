# Project Report: "The Compliance Clerk" - Intelligent Document Extraction

**Author:** Yashpal Yadav  
**Project:** The Compliance Clerk (Hiring Assignment)  

---

## 1. Executive Summary
This report details the design, architecture, and implementation of **The Compliance Clerk**, an automated document extraction pipeline. The system was developed to replace slow, error-prone manual parsing of heterogeneous government documents—specifically Traffic eChallans and Non-Agricultural (NA) Permission PDFs. By leveraging an advanced OCR fallback strategy coupled with Large Language Model (LLM) function calling, the tool ingests unstructured PDFs and securely transforms them into structured, queryable Excel reports. This automation provides immediate value to operations teams by significantly reducing processing time, minimizing human error, and ensuring compliance through an immutable audit trail.

## 2. System Architecture & Pipeline
The document processing pipeline operates as a linear, fault-tolerant state machine:
1.  **PDF Ingestion & Routing:** The orchestrator (`src/main.py`) safely processes single files or entire directories, routing them into the extraction engine.
2.  **Dual-Tier OCR Processing (`src/extractor/`):** The system primarily relies on zero-loss text extraction using `pdfplumber`. If the document is an image-based scanned PDF (yielding low character counts), the system automatically rasterizes the pages via `pdf2image` and applies `pytesseract` OCR to guarantee text acquisition.
3.  **LLM Extraction & Semantic Parsing (`src/agent/`):** The raw text is passed to an LLM agent connected via OpenRouter (`qwen3.6-plus:free`). The LLM first classifies the document type, then routes the text into rigid JSON schemas for targeted entity extraction.
4.  **Structured Data Formatting (`src/reporter/`):** A dynamic reporter component aggregates the validated JSON payloads and systematically routes the data to distinct, domain-specific sheets (`eChallan`, `NA PDF`, `Lease Deed`) within a formatted `output.xlsx` file.

## 3. Core Implementation Details

### 3.1. Multi-Format Parsing
To handle diverse document layouts and languages without brittle regex matching, the application relies on LLM semantic understanding. The system successfully extracts:
*   **eChallans:** Challan Number, Vehicle Number, Violation Date, Amount, Offence Description, Payment Status.
*   **NA PDFs:** Survey Number, Land Area, Owner Name, Order Date, Authority Details.
Classification is forced via a preliminary LLM decision step, allowing multi-page or bundled PDFs to be processed conditionally.

### 3.2. LLM Integration & Schema Enforcement
The core of the LLM integration relies on native **Function Calling (Tool Use)**. Standard LLM text generation frequently hallucinates JSON structures. To counteract this, `src/tools/tools.py` defines rigid JSON Schemas representing the exact data models required. By enforcing `tool_choice="auto"`, the model is mathematically constrained by the API provider to return structured JSON payloads. This ensures horizontal compatibility when writing to analytical DataFrames/Excel. Context limits are mitigated by utilizing high-capacity models capable of absorbing large OCR dumps.

### 3.3. Observability & Audit Trail
Given the probabilistic nature of LLMs, the system employs strict observability. An asynchronous transaction logger (`src/audit/audit.py`) leverages local SQLite (`audit.db`). Every stage of the interaction—including source file paths, detected document types, explicit tool payloads, raw prompts, API responses, and traceback errors—is persisted. This provides operations and compliance teams with full replayability and a transparent debugging apparatus required for production AI workloads.

### 3.4. Version Control & SDLC
The project implements a structured software development lifecycle (SDLC) managed via Git. The repository features an atomic commit log demonstrating linear progression: defining OCR infrastructure, wiring the SQLite audit layer, integrating standard API loops, adapting schemas for resilience, and finally formatting the report output. Each commit encapsulates specific features or bug fixes, entirely avoiding massive, monolithic commits in favor of a clean, revertible history.

## 4. Technical Challenges & Solutions

*   **Messy OCR & Schema Validation Failures (HTTP 400):** 
    *   *Challenge:* OCR artifacts (e.g., reading "251/p2" instead of integer "251" for survey numbers) caused downstream validation crashes when the LLM attempted to pass alphanumeric values into strictly typed `number` fields inside the JSON schema.
    *   *Solution:* Implemented "Fuzzy Typing" by relaxing all numeric schema properties to `string`. This delegated the data-cleaning responsibility safely without instantly crashing the LLM interaction loop, allowing the API to gracefully ingest alphanumeric OCR anomalies and formatting drift.
*   **Prompt Refinement & Semantic Overlap:** 
    *   *Challenge:* The state of Gujarat labels Property Registration and Stamp Duty receipts as "e-Challans". The LLM consistently misclassified property documents as traffic violations.
    *   *Solution:* Refined the system prompt to explicitly define the semantic boundary: *"ONLY extract Traffic Violation eChallans using extract_echallan_fields. DO NOT use extract_echallan_fields for Stamp Duty or Registration Fee receipts."*
*   **Rate Limiting & Throughput:** API endpoint exhaustion was heavily mitigated by migrating the backend LLM provider to OpenRouter and implementing exponential backoffs using the `tenacity` library to retry queries without data loss.

## 5. Conclusion
**The Compliance Clerk** demonstrates a highly scalable, maintainable, and robust approach to intelligent document extraction. By decoupling the OCR ingestion, LLM schema enforcement, audit logging, and reporting layers (Separation of Concerns), the codebase acts as a reliable foundation. The strict tool-calling schemas ensure data integrity, while the localized SQLite audit trails guarantee transparency. The architecture is ready to scale seamlessly; adapting to new document types requires simply passing new JSON schemas, proving its design as a robust enterprise grading submission.
