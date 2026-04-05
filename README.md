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

---

## 🚀 Setup and Installation Instructions

Follow these steps to set up the environment and run the document extraction pipeline.

### Step 1: System Dependencies
The project relies on OCR and PDF parsing libraries which require certain system-level packages to be installed natively on your machine.
*   **Ubuntu/Debian:**
    ```bash
    sudo apt-get update
    sudo apt-get install tesseract-ocr poppler-utils
    ```
*   **macOS:**
    ```bash
    brew install tesseract poppler
    ```

### Step 2: Set up Python Virtual Environment
It is heavily recommended to use a virtual environment to manage dependencies locally.
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Python Dependencies
Install the required Python packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys (.env)
The project relies on an LLM backend to process the text. By default, the script is configured to securely utilize free open-source models via OpenRouter (specifically `qwen/qwen3.6-plus:free`), avoiding strict API quotas.

Create a `.env` file in the root of the project and add your API Key:
```dotenv
OPENROUTER_API_KEY="your_openrouter_api_key_here"
```
*(Note: Be sure your `.env` is listed in your `.gitignore` to prevent exposing your keys!)*

---

## 🏃‍♂️ How to Run the Pipeline

### 1. Place Input Files
Ensure the PDFs you want to process are located in the `Files/` directory.

### 2. Execute the Main Script
Run the orchestrator script from the root dir. Make sure to set the `PYTHONPATH` so the Python interpreter correctly maps the internal `src/` modules:
```bash
PYTHONPATH="$(pwd)" python3 src/main.py --input Files --output data/output
```

### 3. View the Results
Once the script successfully executes, check the outputs:
*   **Extracted Data:** A standardized Excel report will be generated at `data/output/output.xlsx` containing categorized sheets for `NA PDF`, `eChallan`, and `Lease Deed` mappings.
*   **Failed Extractions Logs:** If any files threw exceptions (e.g. unreadable PDF), they'll be logged in `data/output/failed_extractions.txt`.
*   **Audit Trail:** An SQLite database `audit.db` will be live-updated in the project root containing full traces of all processing logic, LLM responses/completions, tokens, schemas, and OCR statuses.
