"""
Main pipeline orchestrator.
Usage: python main.py --input data/input/ --output data/output/
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.progress import track

from src.extractor.extractor import extract_text, detect_doc_type
from src.agent.agent import run_agent
from src.linker.linker import link_records
from src.reporter.reporter import write_excel, write_failed_log
from src.audit.audit import init_db,  log_run_summary

console = Console()

def process_pdf(pdf_path: str) -> tuple[list, str | None]:
    """Process a single PDF. Returns (records, error)."""
    try:
        console.print(f"  📄 Extracting text from [cyan]{Path(pdf_path).name}[/]...")
        text, method = extract_text(pdf_path)
        console.print(f"     Method: [yellow]{method}[/], chars: {len(text)}")
        
        hint_types = detect_doc_type(text)
        console.print(f"     Detected hints: [green]{hint_types}[/]")
        
        console.print(f"  🤖 Running agent...")
        records, classifications = run_agent(pdf_path, text, hint_types)
        console.print(f"     Extracted [green]{len(records)}[/] record(s): {[r['doc_type'] for r in records]}")
        
        return records, None
    
    except Exception as e:
        return [], str(e)
    

def main():
    parser = argparse.ArgumentParser(description="Complience Clerk - Document Extraction Agent")
    parser.add_argument("--input", default="data/input/", help="Input folder with PDFs")
    parser.add_argument("--output", default="data/output/", help="Output folder for Excel")
    args = parser.parse_args()

    init_db()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        console.print("[red]No PDF files found in input directory.[/]")
        return
    
    console.print(f"\n[bold]Compliance Clerk[/] — Processing {len(pdf_files)} file(s)\n")
    
    all_records = []
    failed = []

    for pdf_path in pdf_files:
        console.print(f"\n[bold]→ {pdf_path.name}[/]")
        records, error = process_pdf(str(pdf_path))
        
        if error:
            console.print(f"  [red]✗ Failed: {error}[/]")
            failed.append({"file": pdf_path.name, "reason": error})
        else:
            all_records.extend(records)
    
    # Write Excel directly from extracted records (no linking needed since separated by sheets)
    output_file = output_dir / "output.xlsx"
    write_excel(all_records, str(output_file))
    write_failed_log(failed, str(output_dir))
    
    # Log run summary
    log_run_summary(
        total=len(pdf_files),
        successful=len(pdf_files) - len(failed),
        failed=len(failed),
        output_file=str(output_file)
    )
    
    console.print(f"\n[bold green]✓ Done![/] Output → {output_file}")
    console.print(f"  Audit log → audit.db")
    if failed:
        console.print(f"  [yellow]{len(failed)} file(s) failed → failed_extractions.txt[/]")


if __name__ == "__main__":
    main()