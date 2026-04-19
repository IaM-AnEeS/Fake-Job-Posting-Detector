import pandas as pd
import numpy as np
import joblib
import re
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

DATA_PATH  = os.path.join(os.path.dirname(__file__), 'fake_job_postings.csv')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'model.pkl')

TEXT_COLUMNS = [
    'title', 'company_profile', 'description',
    'requirements', 'benefits', 'location',
    'employment_type', 'required_experience',
    'required_education', 'industry', 'function'
]


def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text).lower()
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def load_data():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"  Rows: {len(df)}")
    print(f"  Fake: {df['fraudulent'].sum()} ({df['fraudulent'].mean()*100:.1f}%)")
    return df


def build_features(df):
    print("Building features...")
    df['combined_text'] = df[TEXT_COLUMNS].apply(
        lambda row: ' '.join(clean_text(str(v)) for v in row.values if pd.notna(v)),
        axis=1
    )
    return df['combined_text'], df['fraudulent']


def train(X_train, y_train):
    print("Training model...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=15000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            stop_words='english'
        )),
        ('model', LogisticRegression(
            class_weight='balanced',
            max_iter=1000,
            C=1.0,
            solver='lbfgs'
        ))
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def evaluate(pipeline, X_test, y_test):
    print("\n" + "="*50)
    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"ACCURACY : {acc*100:.2f}%")
    print("="*50)
    print(classification_report(y_test, y_pred, target_names=['Real','Fake']))

    cm = confusion_matrix(y_test, y_pred)
    print("CONFUSION MATRIX:")
    print(f"  True Real  (correct): {cm[0][0]}")
    print(f"  True Fake  (correct): {cm[1][1]}")
    print(f"  False Fake (wrong)  : {cm[0][1]}")
    print(f"  Missed Fakes (wrong): {cm[1][0]}")
    return acc


def save_model(pipeline):
    os.makedirs('model', exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    size = os.path.getsize(MODEL_PATH) / 1024
    print(f"\nModel saved → {MODEL_PATH} ({size:.1f} KB)")


def predict_sample(pipeline, title, company, description, requirements='', benefits=''):
    text = clean_text(f"{title} {company} {description} {requirements} {benefits}")
    pred   = pipeline.predict([text])[0]
    proba  = pipeline.predict_proba([text])[0]
    conf   = proba[1] if pred == 1 else proba[0]
    label  = "FAKE" if pred == 1 else "REAL"
    print(f"  [{label}] {title} — {conf*100:.1f}% confidence")


if __name__ == '__main__':
    df = load_data()
    X, y = build_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = train(X_train, y_train)
    evaluate(pipeline, X_test, y_test)
    save_model(pipeline)

    print("\nSample predictions:")
    predict_sample(pipeline,
        "Data Entry Work From Home",
        "Global Solutions",
        "No experience needed earn 5000 weekly immediate start no background check",
        "No qualifications needed"
    )
    predict_sample(pipeline,
        "Frontend Engineer React",
        "Stripe",
        "Build payment UI features used by millions collaborate with product and design",
        "3 years React TypeScript testing frameworks"
    )

    print("\nDone! Your model is ready.")