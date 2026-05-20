# Student Dropout Risk Prediction

A machine learning project for predicting student dropout risk from student admission, profile, academic, and economic information.

The final demo is implemented as a web application with:

- **Frontend:** React + Vite
- **Backend:** FastAPI

---

## 1. Clone the repository

```bash
git clone https://github.com/DuongDangHocCode/Student_Dropout_Risk_Prediction.git
cd Student_Dropout_Risk_Prediction
```

---

## 2. Run the backend

Open a terminal and move to the backend folder:

```bash
cd web_demo/backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

### Windows PowerShell

```powershell
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
python -m pip install fastapi uvicorn[standard] pandas numpy scikit-learn joblib
```

Start the FastAPI server:

```bash
python -m uvicorn main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

You can check the API documentation at:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Run the frontend

Open another terminal and move to the frontend folder:

```bash
cd web_demo/frontend
```

Install frontend dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will run at:

```text
http://localhost:5173
```
