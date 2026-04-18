# Fake Job Detector

A complete full-stack application for identifying fraudulent job listings using machine learning. This repository includes a polished **Next.js** frontend, a production-ready **FastAPI** backend, and a training pipeline for building the fraud detection model.

---

## 🌐 Live Demo

**Frontend (Vercel):** [https://fake-job-posting-detector-two.vercel.app/](https://fake-job-posting-detector-two.vercel.app/)

**Backend API (Render):** [https://fake-job-posting-detector-tn3a.onrender.com](https://fake-job-posting-detector-tn3a.onrender.com)

**API Documentation:** [https://fake-job-posting-detector-tn3a.onrender.com/docs](https://fake-job-posting-detector-tn3a.onrender.com/docs)

---

## 🚀 Project Overview

Fake Job Detector helps users verify job postings by analyzing title, company details, salary, description, requirements, and benefits. The frontend collects user input and displays a polished verdict, while the backend powers the prediction with an ML model trained on real and fake job postings.

### What it delivers

- Real-time fake-job detection with confidence scoring
- Modern landing page, form flow, and result dashboard
- API endpoints for health checks and predictions
- Model training pipeline with TF-IDF + Logistic Regression
- Local development and deployment support

---

## 🧩 Tech Stack

- Frontend: `Next.js 16`, `React 19`, `TypeScript`, `ESLint`
- Backend: `FastAPI`, `uvicorn`, `Pydantic`
- ML: `scikit-learn`, `joblib`, `pandas`, `numpy`
- Dataset: `training/fake_job_postings.csv`

---

## 📁 Repository Structure

### Frontend

- `frontend/package.json` — Next.js app scripts and dependencies
- `frontend/app/page.tsx` — homepage and product overview
- `frontend/app/detect/page.tsx` — job posting analysis form
- `frontend/app/result/page.tsx` — prediction results and guidance
- `frontend/lib/api.ts` — API helper for backend requests
- `frontend/app/**/*.module.css` — scoped component styles

### Backend

- `backend/main.py` — FastAPI server and prediction endpoints
- `backend/requirements.txt` — Python dependency manifest
- `backend/render.yaml` — Render deployment configuration
- `backend/model/model.pkl` — serialized ML model output (generated)

### Model training

- `backend/training/train.py` — training pipeline for the classification model
- `backend/training/evaluate.py` — evaluation helper (same file in this repo)
- `backend/training/fake_job_postings.csv` — labeled job posting dataset

---

## ✨ Features

- Predicts whether a job posting is `fake` or `real`
- Shows a confidence score with risk-level categorization
- Supports job title, company, location, salary, description, requirements, benefits
- Includes example fill buttons for quick testing
- Presents actionable recommendations for users
- Backend health checks and ready-to-deploy Render configuration

---

## 🏗️ Backend Details

### API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Basic health status and model loader state |
| `/health` | GET | Detailed health response with model status |
| `/predict` | POST | Returns prediction, confidence, label, and message |

### Prediction contract

Request body:

```json
{
  "title": "Software Engineer",
  "company": "Tech Company",
  "location": "Remote",
  "salary": "$120k/year",
  "description": "Build features and ship production code.",
  "requirements": "3+ years experience in React.",
  "benefits": "Health insurance, remote work."
}
```

Response body:

```json
{
  "prediction": "real",
  "confidence": 0.92,
  "label": "Real Job",
  "message": "This job posting appears to be legitimate."
}
```

### Backend implementation notes

- `backend/main.py` loads `model/model.pkl` on startup
- User input is cleaned with `clean_text()` before prediction
- The app uses CORS with `allow_origins=["*"]` for easy frontend integration
- If model is missing, startup fails with an informative error

---

## 🧠 Model Training Pipeline

The training script builds a text classification pipeline from the fake job dataset.

### Core pipeline

- Text cleaning: lowercasing, HTML tag removal, special character stripping
- Feature extraction: `TfidfVectorizer` with 1-2 grams, `min_df=2`, English stop words
- Classifier: `LogisticRegression` with `class_weight='balanced'`

### How to train the model

```bash
cd backend
python training/train.py
```

This produces the serialized model at:

```bash
backend/model/model.pkl
```

### Training outputs

- Console metrics: accuracy, classification report, confusion matrix
- Sample prediction examples for fake and real jobs

---

## 💻 Local Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ and pip

### 1. Clone and setup

```bash
git clone <repository-url>
cd fake-job-detector
```

### 2. Start the backend locally

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The backend will run at `http://localhost:8000`

### 3. Start the frontend locally

```bash
cd frontend
npm install
npm run dev
```

Open the app at `http://localhost:3000`

### 4. Configure backend URL (for local development)

Create `frontend/.env.local` with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Deployment

The application is currently deployed and running on:

- **Frontend:** Vercel ([https://fake-job-posting-detector-two.vercel.app/](https://fake-job-posting-detector-two.vercel.app/))
- **Backend:** Render ([https://fake-job-posting-detector-tn3a.onrender.com](https://fake-job-posting-detector-tn3a.onrender.com))

### API Endpoints

- **Health Check:** [https://fake-job-posting-detector-tn3a.onrender.com/health](https://fake-job-posting-detector-tn3a.onrender.com/health)
- **Prediction:** [https://fake-job-posting-detector-tn3a.onrender.com/predict](https://fake-job-posting-detector-tn3a.onrender.com/predict)
- **Interactive Docs:** [https://fake-job-posting-detector-tn3a.onrender.com/docs](https://fake-job-posting-detector-tn3a.onrender.com/docs)

---

## 🧪 Frontend Flow

1. The homepage introduces the product with hero content and trust signals.
2. The `/detect` page captures posting details using a multi-field form.
3. Users can populate either a fake or real example instantly.
4. The app submits the data to `/predict` and redirects to `/result`.
5. The results page displays a verdict, confidence gauge, warning flags, and recommended next steps.

---

## 📦 Deployment

### Backend

The provided `backend/render.yaml` config is ready for Render deployment.

Start command:

```yaml
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend

Deploy the `frontend` directory with any Next.js-compatible hosting provider. Ensure `NEXT_PUBLIC_API_URL` points to the live backend.

---

## 🧩 Notes

- The frontend is a stateless UI layer and depends on the backend for prediction logic.
- The backend currently allows all CORS origins for convenience; tighten this for production.
- The model is trained on the `fake_job_postings.csv` dataset in the `backend/training` folder.

---

## 📌 Useful commands

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm start
npm run lint
```

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
python training/train.py
```

---

## 📝 License

This project is intended for educational and demonstration purposes.

---

## 🙌 Contributors

- `frontend/` contains the user interface, interaction flow, and visual design
- `backend/` contains the API server and ML inference logic
- `backend/training/` contains the model training and evaluation pipeline
