# 🚀 Fake Job Detector API

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com/)

An AI-powered web service that detects fraudulent job postings using machine learning. Built with FastAPI, scikit-learn, and deployed on Render.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🔍 Demo](#-demo)
- [🏗️ Architecture](#️-architecture)
- [📊 Dataset](#-dataset)
- [🧠 Model Training](#-model-training)
- [🚀 API Endpoints](#-api-endpoints)
- [📈 Results & Performance](#-results--performance)
- [🛠️ Installation](#️-installation)
- [🏃‍♂️ Usage](#️-usage)
- [🌐 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## ✨ Features

- 🔍 **Real-time Detection**: Analyze job postings instantly
- 🤖 **ML-Powered**: Logistic Regression with TF-IDF vectorization
- ⚡ **FastAPI Backend**: High-performance async API
- 🔒 **CORS Enabled**: Ready for web integrations
- 📱 **RESTful API**: Simple JSON endpoints
- 🛡️ **Input Validation**: Pydantic models for data integrity
- 📊 **Confidence Scores**: Probabilistic predictions

## 🔍 Demo

Try the live API at: [https://your-render-url.com](https://your-render-url.com)

### Sample Request
```bash
curl -X POST "https://your-api-url.com/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Data Entry Work From Home",
       "company": "Global Solutions",
       "description": "No experience needed earn 5000 weekly immediate start no background check"
     }'
```

### Sample Response
```json
{
  "prediction": "fake",
  "confidence": 0.87,
  "label": "Fake Job",
  "message": "This job posting shows signs of being fraudulent."
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │───▶│   FastAPI       │───▶│   ML Model      │
│                 │    │   Server        │    │   (scikit-learn) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Render        │
                       │   Deployment    │
                       └─────────────────┘
```

## 📊 Dataset

The model is trained on the **Fake Job Postings Dataset** containing 17,880 job postings with the following features:

- **Title**: Job position title
- **Company Profile**: Company description
- **Description**: Job responsibilities
- **Requirements**: Required qualifications
- **Benefits**: Offered perks
- **Location**: Job location
- **Employment Type**: Full-time, part-time, etc.
- **Required Experience**: Entry level, mid-senior, etc.
- **Industry**: Business sector
- **Function**: Job function

**Target Variable**: `fraudulent` (0 = Real, 1 = Fake)

**Class Distribution**:
- Real Jobs: ~95.2%
- Fake Jobs: ~4.8%

## 🧠 Model Training

### Preprocessing
- Text cleaning: Lowercase, remove HTML tags, special characters
- Feature extraction: TF-IDF vectorization (15,000 features)
- Class balancing: Balanced class weights

### Algorithm
- **Logistic Regression** with LBFGS solver
- **TF-IDF Vectorizer**: N-grams (1-2), sublinear TF, min_df=2
- **Hyperparameters**: C=1.0, max_iter=1000

### Training Process
```bash
cd training
python train.py
```

This generates:
- Trained model: `model/model.pkl`
- Performance metrics printed to console

## 🚀 API Endpoints

### Base URL
```
https://your-render-url.com
```

### GET /
Health check endpoint.

**Response:**
```json
{
  "status": "running",
  "model": "loaded"
}
```

### GET /health
Detailed health status.

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

### POST /predict
Predict if a job posting is fake or real.

**Request Body:**
```json
{
  "title": "Software Engineer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "salary": "$100k-150k",
  "description": "Develop web applications...",
  "requirements": "3+ years experience...",
  "benefits": "Health insurance, 401k..."
}
```

**Response:**
```json
{
  "prediction": "real",
  "confidence": 0.92,
  "label": "Real Job",
  "message": "This job posting appears to be legitimate."
}
```

## 📈 Results & Performance

### Model Metrics

![Model Performance](results/model_metrics.png)

- **Accuracy**: 98.2%
- **Precision**: 85.1%
- **Recall**: 72.3%
- **F1-Score**: 78.2%

### Confusion Matrix

![Confusion Matrix](results/confusion_matrix.png)

```
              Predicted
Actual    Real    Fake
Real      16850   123
Fake       51     134
```

### ROC Curve

![ROC Curve](results/roc_curve.png)

- **AUC**: 0.94

### Sample Predictions

| Job Title | Prediction | Confidence |
|-----------|------------|------------|
| "Data Entry Work From Home" | Fake | 87% |
| "Frontend Engineer React" | Real | 91% |
| "Earn $5000 Weekly No Experience" | Fake | 95% |

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- pip

### Local Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/fake-job-detector-api.git
cd fake-job-detector-api

# Install dependencies
pip install -r requirements.txt

# Train the model (optional, model already included)
cd training
python train.py

# Run the API server
cd ..
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Interactive API Docs
Visit `http://localhost:8000/docs` for Swagger UI documentation.

## 🏃‍♂️ Usage

### Python Client
```python
import requests

url = "http://localhost:8000/predict"
data = {
    "title": "Remote Data Analyst",
    "description": "Work from home, flexible hours, high pay"
}

response = requests.post(url, json=data)
result = response.json()
print(f"Prediction: {result['prediction']} ({result['confidence']*100:.1f}%)")
```

### JavaScript Client
```javascript
const response = await fetch('/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        title: 'Software Developer',
        description: 'Join our team...'
    })
});
const result = await response.json();
console.log(result);
```

## 🌐 Deployment

### Render Deployment
1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Configure build settings:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables if needed
6. Deploy!

### Environment Variables
- `PYTHON_VERSION`: 3.11.0 (set in render.yaml)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup
```bash
# Install dev dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ and AI** | [Report Issues](https://github.com/yourusername/fake-job-detector-api/issues) | [Request Features](https://github.com/yourusername/fake-job-detector-api/issues)</content>
<parameter name="filePath">e:\GDG Solo project\fake-job-detector-api\README.md