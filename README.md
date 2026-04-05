# NDIS Budget Diagnostic Dashboard

A Flask-based diagnostic tool that predicts NDIS participant budget ranges
using a GLMM-style model with a Gamma response distribution.

---

## Project structure

```
ndis_dashboard/
├── app.py                  # Flask app — model logic + API routes
├── requirements.txt
├── templates/
│   └── index.html          # Main dashboard template
└── static/
    ├── css/
    │   └── dashboard.css
    └── js/
        └── dashboard.js    # UI interactions + fetch calls to /predict
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## API

### POST /predict

Accepts JSON and returns a full prediction object.

**Request**
```json
{
  "age": 34,
  "years_diagnosed": 3,
  "remoteness": 1
}
```

**Response**
```json
{
  "point": 38900,
  "low": 28400,
  "high": 51200,
  "interval_width": 22800,
  "dispersion": 0.284,
  "confidence": "Moderate",
  "confidence_pct": "80%",
  "flag_level": "neutral",
  "flag_text": "Profile within expected parameters...",
  "remoteness_label": "Inner regional",
  "contributions": {
    "Age": 4200,
    "Time since diagnosis": 5800,
    "Remoteness": 3800
  }
}
```

**Remoteness values**
| Value | Label |
|-------|-------|
| 0 | Major city |
| 1 | Inner regional |
| 2 | Outer regional |
| 3 | Remote |
| 4 | Very remote |

---

## Replacing placeholder coefficients

All model coefficients are in the `MODEL_CONFIG` dictionary at the top of `app.py`.
Once you have fitted a real GLMM on NDIS participant data, replace these values
with the estimated coefficients from your model. The compute_budget() function
documents which parameter maps to which part of the GLMM formula.

---

## Important disclaimer

The current coefficients are **placeholders for prototyping only**.
They are not derived from any NDIS dataset or published research.
Do not use this tool in any real interviewer or planning context
until the coefficients have been replaced with properly fitted values.
