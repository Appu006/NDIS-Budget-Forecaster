from flask import Flask, render_template, request, jsonify
import math

#app = Flask(__name__)
app = Flask(__name__, template_folder='template', static_folder='static')

MODEL_CONFIG = {
    "baseline": 57903.28,          # Intercept: floor budget before participant characteristics
    "age_mod_slope": 70,       # Linear slope: dollars per year relative to reference age 34
    "age_reference": 34,        # Reference age for the linear modifier
    "age_factors": {            # Multiplicative group effects on baseline
        "child":   {"min": 0,  "max": 17,  "factor": 0.80},
        "young":   {"min": 18, "max": 39,  "factor": 1.00},
        "middle":  {"min": 40, "max": 59,  "factor": 1.20},
        "older":   {"min": 60, "max": 999, "factor": 1.30},
    },
    "diag_log_multiplier": 2800,    # Scales logarithmic effect of time since diagnosis
    "remote_step": 3800,            # Dollars added per remoteness level (0-4)
    "base_dispersion": 0.28,        # Base Gamma dispersion (phi) — controls interval width
    "remote_dispersion_step": 0.04, # Dispersion widens by this amount per remoteness level
    "recent_diag_dispersion": 0.06, # Extra dispersion for recently diagnosed (< 2 years)
    "interval_z": 1.28,             # Z-score for 80% prediction interval
}

REMOTENESS_LABELS = [
    "Major city",
    "Inner regional",
    "Outer regional",
    "Remote",
    "Very remote",
]


def get_age_factor(age: int) -> float:
    """Return the multiplicative age group factor."""
    for group in MODEL_CONFIG["age_factors"].values():
        if group["min"] <= age <= group["max"]:
            return group["factor"]
    return 1.0


def compute_budget(age: int, years_diagnosed: int, remoteness: int) -> dict:
    """
    Compute the predicted NDIS budget range for a participant.

    Uses a GLMM-style formula:
        mu = baseline * age_factor + diag_effect + remote_effect + age_mod
        low  = mu * exp(-z * phi)
        high = mu * exp(+z * phi)

    Parameters
    ----------
    age : int
        Participant age in years.
    years_diagnosed : int
        Years since the participant received their diagnosis.
    remoteness : int
        ABS remoteness category (0 = Major city, 4 = Very remote).

    Returns
    -------
    dict with keys: point, low, high, dispersion, contributions
    """
    cfg = MODEL_CONFIG

    age_factor = get_age_factor(age)
    age_mod = (age - cfg["age_reference"]) * cfg["age_mod_slope"]
    diag_effect = math.log1p(years_diagnosed) * cfg["diag_log_multiplier"]
    remote_effect = remoteness * cfg["remote_step"]

    mu = cfg["baseline"] * age_factor + diag_effect + remote_effect + age_mod

    # Dispersion widens with remoteness and recent diagnosis
    phi = cfg["base_dispersion"]
    phi += remoteness * cfg["remote_dispersion_step"]
    if years_diagnosed < 2:
        phi += cfg["recent_diag_dispersion"]

    z = cfg["interval_z"]
    low = mu * math.exp(-z * phi)
    high = mu * math.exp(z * phi)

    # Individual variable contributions for breakdown panel
    contributions = {
        "Age": round(abs(age_mod + (age_factor - 1.0) * cfg["baseline"])),
        "Time since diagnosis": round(diag_effect),
        "Remoteness": round(remote_effect),
    }

    # Confidence label based on dispersion
    if phi < 0.30:
        confidence = "High"
        confidence_pct = "85%"
    elif phi < 0.38:
        confidence = "Moderate"
        confidence_pct = "80%"
    else:
        confidence = "Low"
        confidence_pct = "72%"

    # Contextual flag for the interviewer
    if remoteness >= 3:
        flag_level = "alert"
        flag_text = (
            "High remoteness detected — service access is likely limited. "
            "Budget may require upward adjustment for travel and coordination support."
        )
    elif years_diagnosed <= 1:
        flag_level = "warn"
        flag_text = (
            "Recently diagnosed — support needs may still be stabilising. "
            "Revisit budget estimate at 12-month review."
        )
    elif age >= 65:
        flag_level = "warn"
        flag_text = (
            "Older participant — consider overlap with aged care services. "
            "Confirm primary funding stream before finalising."
        )
    else:
        flag_level = "neutral"
        flag_text = (
            "Profile within expected parameters. "
            "Use predicted range as a baseline for the interview conversation."
        )

    return {
        "point": round(mu),
        "low": round(low),
        "high": round(high),
        "interval_width": round(high - low),
        "dispersion": round(phi, 3),
        "confidence": confidence,
        "confidence_pct": confidence_pct,
        "flag_level": flag_level,
        "flag_text": flag_text,
        "contributions": contributions,
        "remoteness_label": REMOTENESS_LABELS[remoteness],
    }


@app.route("/")
def index():
    return render_template("index.html", remoteness_labels=REMOTENESS_LABELS)


@app.route("/predict", methods=["POST"])
def predict():
    """
    POST /predict
    Accepts JSON: { "age": int, "years_diagnosed": int, "remoteness": int }
    Returns JSON with full prediction output.
    """
    data = request.get_json()

    # Input validation
    errors = {}
    age = data.get("age")
    years_diagnosed = data.get("years_diagnosed")
    remoteness = data.get("remoteness")

    if not isinstance(age, int) or not (5 <= age <= 85):
        errors["age"] = "Age must be an integer between 5 and 85."
    if not isinstance(years_diagnosed, int) or not (0 <= years_diagnosed <= 30):
        errors["years_diagnosed"] = "Years diagnosed must be between 0 and 30."
    if not isinstance(remoteness, int) or not (0 <= remoteness <= 4):
        errors["remoteness"] = "Remoteness must be between 0 and 4."

    if errors:
        return jsonify({"error": errors}), 400

    result = compute_budget(age, years_diagnosed, remoteness)
    return jsonify(result)


#if __name__ == "__main__":
#    app.run(debug=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
