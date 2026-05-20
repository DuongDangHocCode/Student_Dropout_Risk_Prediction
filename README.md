# Student Dropout Risk Prediction

A Streamlit web app for predicting student dropout risk using a trained machine learning model.

## Project structure

```text
Student_Dropout_Risk_Prediction/
│
├── app.py
├── Student_Dropout_Risk_Prediction.ipynb
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

Activate it:

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

## Run the Streamlit app

Make sure the trained model checkpoint is placed inside the `models/` folder:

```text
models/best_model_Random_Forest.pkl
```

Then run:

```bash
streamlit run app.py
```

After running the command, open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Train the model again

If the model file is missing, run the notebook:

```text
Student_Dropout_Risk_Prediction.ipynb
```

Run all cells until the final checkpoint saving step. The notebook will save the trained model bundle into the `models/` folder.

## Note

The app uses the same preprocessing and feature engineering steps as the training notebook, so the saved model bundle must include:

- the trained model
- the preprocessor
- selected raw features
- processed feature names
- target label mapping
