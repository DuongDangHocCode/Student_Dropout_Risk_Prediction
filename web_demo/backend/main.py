from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mappings import MAPPINGS


APP_TITLE = "Student Dropout Risk Prediction API"
MODEL_PATH = Path("models/best_model_Random_Forest.pkl")


class PredictRequest(BaseModel):
    marital_status: float
    application_mode: float
    application_order: float
    course: float
    daytime_evening_attendance: float
    previous_qualification: float
    previous_qualification_grade: float
    nacionality: float
    mothers_qualification: float
    fathers_qualification: float
    mothers_occupation: float
    fathers_occupation: float
    admission_grade: float
    displaced: float
    educational_special_needs: float
    debtor: float
    tuition_fees_up_to_date: float
    gender: float
    scholarship_holder: float
    age_at_enrollment: float
    international: float
    curricular_units_1st_sem_credited: float
    curricular_units_1st_sem_enrolled: float
    curricular_units_1st_sem_evaluations: float
    curricular_units_1st_sem_approved: float
    curricular_units_1st_sem_grade: float
    curricular_units_1st_sem_without_evaluations: float
    curricular_units_2nd_sem_credited: float
    curricular_units_2nd_sem_enrolled: float
    curricular_units_2nd_sem_evaluations: float
    curricular_units_2nd_sem_approved: float
    curricular_units_2nd_sem_grade: float
    curricular_units_2nd_sem_without_evaluations: float
    unemployment_rate: float
    inflation_rate: float
    gdp: float


class PredictResponse(BaseModel):
    prediction: str
    is_dropout: bool
    dropout_probability: float | None
    dropout_percent: float | None
    risk_level: str | None
    color: str
    model_name: str


app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Feature engineering - giữ giống notebook train model
# =========================================================
def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = (
        dataframe.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return dataframe


def add_engineered_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    eps = 1e-6

    dataframe["approval_rate_1st_sem"] = (
        dataframe["curricular_units_1st_sem_(approved)"] /
        (dataframe["curricular_units_1st_sem_(enrolled)"] + eps)
    )

    dataframe["approval_rate_2nd_sem"] = (
        dataframe["curricular_units_2nd_sem_(approved)"] /
        (dataframe["curricular_units_2nd_sem_(enrolled)"] + eps)
    )

    dataframe["total_approved_units"] = (
        dataframe["curricular_units_1st_sem_(approved)"] +
        dataframe["curricular_units_2nd_sem_(approved)"]
    )

    dataframe["total_enrolled_units"] = (
        dataframe["curricular_units_1st_sem_(enrolled)"] +
        dataframe["curricular_units_2nd_sem_(enrolled)"]
    )

    dataframe["overall_approval_rate"] = (
        dataframe["total_approved_units"] /
        (dataframe["total_enrolled_units"] + eps)
    )

    dataframe["grade_change"] = (
        dataframe["curricular_units_2nd_sem_(grade)"] -
        dataframe["curricular_units_1st_sem_(grade)"]
    )

    dataframe["avg_semester_grade"] = (
        dataframe["curricular_units_1st_sem_(grade)"] +
        dataframe["curricular_units_2nd_sem_(grade)"]
    ) / 2

    dataframe["financial_risk"] = (
        dataframe["debtor"].astype(int) +
        (1 - dataframe["tuition_fees_up_to_date"].astype(int))
    )

    return dataframe


@lru_cache(maxsize=1)
def load_checkpoint() -> dict[str, Any]:
    path = MODEL_PATH

    if not path.exists():
        candidates = sorted(Path("models").glob("best_model_*.pkl"))
        if candidates:
            path = candidates[0]

    if not path.exists():
        raise FileNotFoundError(
            "Không tìm thấy checkpoint. Hãy đặt file best_model_Random_Forest.pkl trong backend/models/."
        )

    return joblib.load(path)


def get_model_from_checkpoint(checkpoint: dict[str, Any]):
    model_name = checkpoint.get("best_model_name", "Unknown model")

    if "model" in checkpoint:
        return checkpoint["model"], model_name

    if "models" in checkpoint and model_name in checkpoint["models"]:
        return checkpoint["models"][model_name], model_name

    raise KeyError("Checkpoint không có key 'model' hoặc 'models'.")


def build_raw_input(payload: PredictRequest) -> dict[str, float]:
    data = payload.model_dump()

    # Key bên frontend đặt dạng dễ đọc; key ở đây đổi về đúng tên cột gốc trong dataset/notebook.
    return {
        "marital_status": data["marital_status"],
        "application_mode": data["application_mode"],
        "application_order": data["application_order"],
        "course": data["course"],
        "daytime/evening_attendance": data["daytime_evening_attendance"],
        "previous_qualification": data["previous_qualification"],
        "previous_qualification_(grade)": data["previous_qualification_grade"],
        "nacionality": data["nacionality"],
        "mother's_qualification": data["mothers_qualification"],
        "father's_qualification": data["fathers_qualification"],
        "mother's_occupation": data["mothers_occupation"],
        "father's_occupation": data["fathers_occupation"],
        "admission_grade": data["admission_grade"],
        "displaced": data["displaced"],
        "educational_special_needs": data["educational_special_needs"],
        "debtor": data["debtor"],
        "tuition_fees_up_to_date": data["tuition_fees_up_to_date"],
        "gender": data["gender"],
        "scholarship_holder": data["scholarship_holder"],
        "age_at_enrollment": data["age_at_enrollment"],
        "international": data["international"],
        "curricular_units_1st_sem_(credited)": data["curricular_units_1st_sem_credited"],
        "curricular_units_1st_sem_(enrolled)": data["curricular_units_1st_sem_enrolled"],
        "curricular_units_1st_sem_(evaluations)": data["curricular_units_1st_sem_evaluations"],
        "curricular_units_1st_sem_(approved)": data["curricular_units_1st_sem_approved"],
        "curricular_units_1st_sem_(grade)": data["curricular_units_1st_sem_grade"],
        "curricular_units_1st_sem_(without_evaluations)": data["curricular_units_1st_sem_without_evaluations"],
        "curricular_units_2nd_sem_(credited)": data["curricular_units_2nd_sem_credited"],
        "curricular_units_2nd_sem_(enrolled)": data["curricular_units_2nd_sem_enrolled"],
        "curricular_units_2nd_sem_(evaluations)": data["curricular_units_2nd_sem_evaluations"],
        "curricular_units_2nd_sem_(approved)": data["curricular_units_2nd_sem_approved"],
        "curricular_units_2nd_sem_(grade)": data["curricular_units_2nd_sem_grade"],
        "curricular_units_2nd_sem_(without_evaluations)": data["curricular_units_2nd_sem_without_evaluations"],
        "unemployment_rate": data["unemployment_rate"],
        "inflation_rate": data["inflation_rate"],
        "gdp": data["gdp"],
    }


def predict_from_raw_input(raw_input_dict: dict[str, float], checkpoint: dict[str, Any]) -> PredictResponse:
    model, model_name = get_model_from_checkpoint(checkpoint)

    input_df = pd.DataFrame([raw_input_dict])
    input_df = normalize_columns(input_df)
    input_df = add_engineered_features(input_df)

    selected_raw_features = checkpoint["selected_raw_features"]
    missing_cols = [col for col in selected_raw_features if col not in input_df.columns]
    if missing_cols:
        raise ValueError(f"Thiếu cột đầu vào: {missing_cols}")

    input_df = input_df[selected_raw_features].copy()
    for col in selected_raw_features:
        input_df[col] = pd.to_numeric(input_df[col], errors="raise")

    processed = checkpoint["preprocessor"].transform(input_df)
    if hasattr(processed, "toarray"):
        processed = processed.toarray()

    input_processed = pd.DataFrame(
        processed,
        columns=checkpoint["processed_feature_names"],
    )

    pred = model.predict(input_processed)[0]
    try:
        pred_key = int(pred)
    except (TypeError, ValueError):
        pred_key = pred

    inverse_mapping = checkpoint.get("inverse_target_mapping", {0: "Graduate", 1: "Dropout"})
    prediction_label = inverse_mapping.get(pred_key, inverse_mapping.get(str(pred_key), str(pred_key)))
    is_dropout = str(prediction_label).strip().lower() == "dropout"

    dropout_probability = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(input_processed)[0]
        classes = list(getattr(model, "classes_", []))

        if 1 in classes:
            dropout_idx = classes.index(1)
        elif "Dropout" in classes:
            dropout_idx = classes.index("Dropout")
        else:
            dropout_idx = 1 if len(proba) > 1 else 0

        dropout_probability = float(proba[dropout_idx])

    risk_level = None
    dropout_percent = None
    if dropout_probability is not None:
        dropout_percent = dropout_probability * 100
        if dropout_probability >= 0.70:
            risk_level = "High / Cao"
        elif dropout_probability >= 0.40:
            risk_level = "Medium / Trung bình"
        else:
            risk_level = "Low / Thấp"

    return PredictResponse(
        prediction=str(prediction_label),
        is_dropout=is_dropout,
        dropout_probability=dropout_probability,
        dropout_percent=dropout_percent,
        risk_level=risk_level,
        color="#ef4444" if is_dropout else "#22c55e",
        model_name=str(model_name),
    )


@app.get("/")
def root():
    return {"message": APP_TITLE}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/options")
def get_options():
    return MAPPINGS


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    try:
        checkpoint = load_checkpoint()
        raw_input = build_raw_input(payload)
        return predict_from_raw_input(raw_input, checkpoint)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
