# LegalAudit

A rule-based expert system that checks Malaysian employment contracts and residential tenancy agreements against the law, then explains every finding.

Upload a contract (PDF, scan, image or plain text), pick the document type, and get back a risk-rated report that cites the exact statute behind each issue. The report can be exported as a PDF.

> Built as a university group project for an AI principles course. It is a learning project, not legal advice.

<!-- Add a screenshot or GIF here: ![LegalAudit demo](docs/demo.gif) -->

## What it does

- **38 legal rules** (20 employment, 18 tenancy) mapped to real Malaysian statutes
- **Multi-layer text extraction**: PyMuPDF, then pdfplumber, then Tesseract OCR for scanned files and images
- **Document relevance check** that rejects the wrong type of document before analysis
- **Clause validation** beyond keyword matching, such as pulling out the salary figure and checking notice period length
- **Explanation facility** that shows why each rule fired, with the matched text, the statute and a recommended fix
- **Conflict resolution** so overlapping rules don't produce duplicate or contradictory findings
- **PDF compliance report** export

## How it works

```
Upload / paste text
        |
   OCR processor ---- PyMuPDF -> pdfplumber -> Tesseract
        |
 Relevance check ---- is this really an employment / tenancy contract?
        |
 Inference engine ---- evaluates rules from the knowledge base
        |
 Conflict resolution -> Explanation facility
        |
  JSON report -> Web UI -> PDF export
```

Each rule in `knowledge_base.py` has an ID, statute reference, keywords, a check type, a risk level, a priority and a recommendation. A rule either flags a clause that is missing (`presence`) or a risky clause that is there (`risk_keyword`). Because the rules are data and not code, adding a new one doesn't require touching the engine.

## Acts covered

**Employment:** Employment Act 1955, Contracts Act 1950, EPF Act 1991, Employees' Social Security Act 1969, Minimum Wages Order 2022, Human Resources Development Act 2001

**Tenancy:** Contracts Act 1950, Stamp Act 1949, National Land Code 1965

## Tech stack

Python, Flask, PyMuPDF, pdfplumber, Tesseract (pytesseract), ReportLab, vanilla HTML/CSS/JS

## Getting started

**1. Install Tesseract** (only needed for scanned documents and images)

- Windows: https://github.com/UB-Mannheim/tesseract/wiki (add it to PATH)
- macOS: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

**2. Set up the project**

```bash
git clone https://github.com/mohammedadalachi/legalaudit.git
cd legalaudit
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run it**

```bash
python app.py
```

Open http://localhost:5000

## Try it

Paste the contents of `samples/sample_employment.txt` and select *Employment Contract*, or paste `samples/sample_tenancy.txt` and select *Residential Tenancy Agreement*. Both samples contain deliberate violations so you can see the findings and explanations.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Web interface |
| `/analyse` | POST | Analyse a file upload (`multipart/form-data`) or pasted text (`{"text": "...", "doc_type": "employment"}`) |
| `/download-report` | POST | Generate a PDF from an analysis result |
| `/health` | GET | Liveness check |

## Project structure

```
legalaudit/
├── app.py                 Flask server and routes
├── knowledge_base.py      The 38 legal rules
├── inference_engine.py    Rule evaluation, conflict resolution, explanations
├── ocr_processor.py       Multi-layer text extraction
├── pdf_report.py          PDF report generator
├── templates/index.html   Web interface
├── samples/               Test contracts
└── requirements.txt
```

## Limitations

- Matching is keyword-based, so unusual wording can be missed
- Rules reflect the law as written in the covered Acts and may not track later amendments
- OCR quality depends on scan quality
- Output is informational only and is not a substitute for a lawyer

## Team

Built as a university group project.

- [Dalachi Mohammed Abderrahmane](https://github.com/mohammedadalachi)


## License

MIT. See [LICENSE](LICENSE).

