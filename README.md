# DarkDetect

### Automated Dark Pattern Detection for Websites

**DarkDetect** is a web-based tool that analyses websites for deceptive user-interface and user-experience techniques, commonly known as **dark patterns**.

Enter a website URL and DarkDetect crawls the page, analyses its content and structure using a combination of **rule-based heuristics and machine-learning classification**, and produces an accessible report explaining which dark patterns were detected and why they matter.

**Live application:** [dark-patterns-detector.vercel.app]

---

## Overview

Dark patterns are design practices that intentionally influence users towards decisions they may not otherwise make. They can include misleading visual emphasis, hidden costs, manipulative language, disguised advertising, artificial urgency, and difficult-to-cancel services.

DarkDetect aims to make these techniques easier to identify by automatically examining webpages and presenting its findings in a clear, human-readable format.

The system combines:

* **Web scraping and content extraction**
* **Rule-based detection heuristics**
* **Machine-learning text classification**
* **Structural webpage analysis**
* **Evidence-based detection results**
* **A React-based visual reporting interface**
* **Local analysis history**

---

## Features

### 🔍 Automated Website Analysis

Submit a URL and DarkDetect retrieves and analyses the webpage automatically.

The analysis considers both visible content and webpage structure rather than relying exclusively on keyword matching.

### 🧠 Hybrid Detection Engine

DarkDetect combines two complementary approaches:

**Rule-based heuristics**

Identify recognisable signals such as urgency language, countdown-like elements, suspicious advertising structures, and other predefined patterns.

**Machine learning**

A trained text-classification pipeline analyses webpage content to identify language associated with dark-pattern categories.

Combining these approaches allows the system to consider both explicit structural signals and more subtle linguistic patterns.

### 📊 Evidence-Based Reports

Detected patterns are presented with contextual information explaining:

* What was detected
* Which category it belongs to
* Why the finding matters
* Evidence from the analysed page
* The reasoning behind the detection

### 🗂️ Analysis History

Previous analyses can be stored locally and accessed through the application's History interface, allowing results to be reviewed or analysed again.

### 🎯 Six Detection Categories

DarkDetect currently focuses on six categories:

| ID   | Category               | Description                                                                       |
| ---- | ---------------------- | --------------------------------------------------------------------------------- |
| DP-1 | **Misdirection**       | Visual or textual techniques that steer users towards a particular choice         |
| DP-2 | **Hidden Costs**       | Fees or additional charges that are disclosed late in the user journey            |
| DP-3 | **Confirmshaming**     | Guilt-inducing language used to discourage users from opting out                  |
| DP-4 | **Disguised Ads**      | Advertising presented in a way that resembles normal content                      |
| DP-5 | **Forced Continuity**  | Subscription or renewal mechanisms that make continued payment difficult to avoid |
| DP-6 | **Urgency / Scarcity** | Countdown timers, limited-stock claims, or other pressure-inducing signals        |

---

## How It Works

```text
                         ┌──────────────────┐
                         │   Website URL    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Web Scraper      │
                         │ HTML / DOM /     │
                         │ Visible Content  │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │     Detection Engine     │
                    │                          │
                    │  Rule-Based Heuristics   │
                    │           +              │
                    │  ML Text Classification  │
                    │           +              │
                    │  Structural Analysis     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │ Detection        │
                         │ Findings &       │
                         │ Evidence         │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ DarkDetect       │
                         │ Web Interface    │
                         │ & Report         │
                         └──────────────────┘
```

---

## Architecture

The project is organised into separate components for scraping, detection, presentation, evaluation, and supporting data.

```text
dark-patterns/
│
├── api/
│   └── main.py                 # FastAPI application
│
├── detection_engine/
│   └── ...                     # Rules, ML classification & analysis
│
├── scraper/
│   └── ...                     # Webpage retrieval & content extraction
│
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json            # React frontend
│
├── data/
│   ├── models/                 # Trained ML models
│   ├── labelled/               # Labelled training/evaluation data
│   └── raw/                    # Raw webpage data
│
├── evaluation/
│   └── ...                     # Model/system evaluation
│
├── docs/
│   └── ...                     # Supporting project documentation
│
├── tests/
│   └── ...                     # Automated tests
│
├── requirements.txt
├── Dockerfile
├── render.yaml
├── pytest.ini
└── README.md
```

---

## Technology Stack

### Backend

* **Python**
* **FastAPI**
* **Uvicorn**
* **scikit-learn**
* **Playwright**
* **BeautifulSoup / HTML parsing**

### Frontend

* **React**
* **JavaScript**
* **CSS**
* **Local Storage** for analysis history

### Machine Learning

The detection engine uses a trained scikit-learn classification pipeline combining TF-IDF text representation with logistic regression classification.

The trained model is loaded by the backend and used alongside deterministic detection rules.

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/HanJay09/dark-patterns.git
cd dark-patterns
```

### 2. Create a Python virtual environment

#### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers

```bash
playwright install
```

### 5. Start the API

From the project root:

```bash
uvicorn api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 6. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm start
```

The frontend will then be available through the React development server.

---

## API

The backend exposes an analysis endpoint that accepts a website URL and returns the detected dark-pattern findings.

### Analyse a URL

```http
POST /analyse
```

Example request:

```json
{
  "url": "https://example.com"
}
```

The response contains the analysis results, including detected categories, findings, evidence, and supporting information used by the frontend report.

The API also exposes automatically generated documentation when running FastAPI locally:

```text
http://127.0.0.1:8000/docs
```

---

## Example Analysis

A typical analysis follows this process:

```text
1. User submits a URL
          ↓
2. DarkDetect retrieves the webpage
          ↓
3. Visible text and structural information are extracted
          ↓
4. Detection rules inspect page signals
          ↓
5. ML classifier analyses relevant text
          ↓
6. Findings from the detection pipeline are combined
          ↓
7. Evidence and explanations are generated
          ↓
8. Results are displayed in the DarkDetect report
```

The system is designed to provide **explanations rather than simply returning a classification label**, making the results easier to interpret and evaluate.

---

## Project Status

DarkDetect is a completed MSc project prototype demonstrating an end-to-end approach to automated dark-pattern detection.

### Current capabilities

* [x] Webpage crawling and content extraction
* [x] Rule-based dark-pattern detection
* [x] Machine-learning text classification
* [x] Six dark-pattern categories
* [x] Evidence-based findings
* [x] FastAPI backend
* [x] React frontend
* [x] Analysis report interface
* [x] Local analysis history
* [x] Deployment configuration

The system should be considered a **research and evaluation prototype**, rather than a definitive authority on whether a website is intentionally deceptive.

---

## Limitations

Automated dark-pattern detection is inherently difficult. A webpage can contain language or design elements that resemble a dark pattern without necessarily being intentionally deceptive.

DarkDetect therefore provides **indications and evidence**, rather than definitive legal or ethical judgements.

Current limitations include:

* Detection is limited to the six supported categories.
* Website behaviour can change dynamically.
* Some interactions require user actions that are difficult to reproduce automatically.
* Machine-learning predictions depend on the quality and coverage of the training data.
* False positives and false negatives are possible.
* Detection results should be interpreted in context.

These limitations are particularly important when evaluating real-world websites.

---

## Research Context

DarkDetect was developed as an MSc project at **Queen Mary University of London** during the 2025–26 academic year.

The project investigates how automated web analysis, heuristic detection, and machine-learning techniques can be combined to identify potentially deceptive interface patterns.

The system is intended to support research and experimentation around transparent and user-centred web design.

---

## Responsible Use

DarkDetect is intended for **research, education, usability evaluation, and responsible website analysis**.

Detection results should not be treated as definitive evidence that a website or organisation is deliberately manipulating users.

When using the system against third-party websites, users should respect applicable terms of service, access restrictions, copyright, privacy requirements, and relevant laws.

---

## License

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for the full license text.

---

## Author

**Han Jay Tan**

MSc Project — Queen Mary University of London
2025–26

---

## Acknowledgements

This project was developed as part of postgraduate research into automated detection of deceptive user-interface and user-experience patterns.

Special thanks to the academic supervision and research support provided throughout the project.

---

## Links

* **Live application:** [DarkDetect](https://dark-patterns-detector.vercel.app/?utm_source=chatgpt.com)
* **Repository:** [GitHub — HanJay09/dark-patterns](https://github.com/HanJay09/dark-patterns?utm_source=chatgpt.com)
