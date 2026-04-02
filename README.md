# Project Title: "The Compliance Clerk" – Intelligent Document Extraction

## Objective
Build a robust Python-based tool that automates the extraction of key data points from heterogeneous PDF documents (eChallan and NA (Non-Agricultural) Permission documents) and consolidates them into a standardized Excel/CSV report.

## Background
Our operations team manually parses hundreds of legal and government documents daily. This process is slow and prone to human error. Your goal is to build an LLM-powered pipeline that "reads" these documents like a human would and outputs structured data.

## 🛠️ Core Requirements (The "Must-Haves")

**1. Multi-Format Parsing:**
*   **eChallan:** Extract fields like Challan Number, Vehicle Number, Violation Date, Amount, Offence Description, and Payment Status.
*   **NA PDF:** Extract Survey Number, Land Area, Owner Name, Order Date, and Authority Details.

**2. LLM Integration:** 
Use an LLM (e.g., GPT-4o, Claude 3.5, or a local Llama-3 model) to handle the extraction. You must implement a "Schema Enforcement" strategy to ensure the LLM output is always valid JSON before saving to Excel.

**3. Audit Trail (LLM Logs):** 
All raw LLM prompts and responses must be saved in a local SQLite database or a JSONL file for debugging and quality audit.

**4. Version Control (Atomic Commits):** 
Use Git to track your progress. We strictly do **not** want a "bulk commit" (one massive commit at the end of the project).
*   We want to see the evolution of your logic: show us how you refined your prompts, how you handled edge cases in OCR, and how you structured your classes.
*   Aim for meaningful, descriptive commit messages for each feature or bug fix.
