# Student Dropout Risk Prediction

A simple Streamlit web app for predicting student dropout risk using a trained machine learning model.

## Project structure

```text
Student_Dropout_Risk_Prediction/
│
├── app.py
├── requirements.txt
├── README.md
└── models/
    └── best_model_Random_Forest.pkl
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/DuongDangHocCode/Student_Dropout_Risk_Prediction.git
cd Student_Dropout_Risk_Prediction
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate
```

```bash
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` file is only for running `app.py`.

## Required model file

Before running the app, make sure the trained model checkpoint is placed in the `models/` folder:

```text
models/best_model_Random_Forest.pkl
```

If your model file has another name, it should still follow this format:

```text
models/best_model_*.pkl
```

## Run the app

```bash
streamlit run app.py
```

After running the command, open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Note

This repository includes the Streamlit app for prediction.  
The model training process is done separately in the notebook, and the final trained model should be saved into the `models/` folder before running the app.
