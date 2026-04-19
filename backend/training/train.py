import pandas as pd
import numpy as np
import joblib
import re
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import hstack, csr_matrix
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

# These binary/numeric columns are strong fraud signals — do NOT ignore them
BINARY_COLUMNS = ['telecommuting', 'has_company_logo', 'has_questions']


# ── Text helpers ─────────────────────────────────────────────────────────────

def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text).lower()
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ── Feature engineering ───────────────────────────────────────────────────────

def engineer_features(df):
    """
    Create extra numeric features from the raw DataFrame.
    These capture signals that TF-IDF alone cannot see.
    """
    feats = pd.DataFrame(index=df.index)

    # -- Binary columns (already clean 0/1) -----------------------------------
    feats['telecommuting']    = df['telecommuting'].fillna(0).astype(float)
    feats['has_company_logo'] = df['has_company_logo'].fillna(0).astype(float)
    feats['has_questions']    = df['has_questions'].fillna(0).astype(float)

    # -- Missingness flags (missing fields correlate with fraud) --------------
    feats['missing_salary']      = df['salary_range'].isna().astype(float)
    feats['missing_company']     = df['company_profile'].isna().astype(float)
    feats['missing_requirements']= df['requirements'].isna().astype(float)
    feats['missing_benefits']    = df['benefits'].isna().astype(float)
    feats['missing_dept']        = df['department'].isna().astype(float)

    # -- Text length signals --------------------------------------------------
    feats['desc_len']    = df['description'].fillna('').apply(len)
    feats['req_len']     = df['requirements'].fillna('').apply(len)
    feats['company_len'] = df['company_profile'].fillna('').apply(len)

    # Normalise lengths to 0-1 range
    for col in ['desc_len', 'req_len', 'company_len']:
        max_val = feats[col].max()
        if max_val > 0:
            feats[col] = feats[col] / max_val

    # -- Suspicious keyword count in description ------------------------------
    SUSPICIOUS = [
        'no experience', 'earn from home', 'weekly pay', 'gift card',
        'wire transfer', 'no interview', 'immediate start', 'whatsapp',
        'telegram', 'bank account', 'ssn', 'social security',
        'money transfer', 'work from home', 'be your own boss',
        'unlimited earning', 'passive income'
    ]
    def count_suspicious(text):
        text = str(text).lower()
        return sum(1 for kw in SUSPICIOUS if kw in text)

    desc = df['description'].fillna('') + ' ' + df['title'].fillna('')
    feats['suspicious_kw_count'] = desc.apply(count_suspicious)

    return feats


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"  Rows : {len(df)}")
    print(f"  Fake : {df['fraudulent'].sum()}  ({df['fraudulent'].mean()*100:.1f}%)")
    return df


# ── Build combined feature matrix ─────────────────────────────────────────────

def build_features(df):
    print("Building features...")

    # 1. Combined text for TF-IDF
    combined_text = df[TEXT_COLUMNS].apply(
        lambda row: ' '.join([clean_text(v) for v in row]),
        axis=1
    )

    # 2. Engineered numeric features
    numeric_feats = engineer_features(df)

    labels = df['fraudulent']
    return combined_text, numeric_feats, labels


# ── Training ──────────────────────────────────────────────────────────────────

def train(text_train, numeric_train, y_train):
    print("Training model...")

    # Step 1 — TF-IDF on text
    tfidf = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
        stop_words='english'
    )
    X_text = tfidf.fit_transform(text_train)

    # Step 2 — Stack with numeric features
    X_numeric = csr_matrix(numeric_train.values.astype(float))
    X_combined = hstack([X_text, X_numeric])

    # Step 3 — Train Random Forest (much better than LogisticRegression here)
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_combined, y_train)

    # Bundle everything needed for prediction
    model_bundle = {
        'tfidf': tfidf,
        'clf': clf,
        'numeric_columns': list(numeric_train.columns)
    }
    return model_bundle


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate(model_bundle, text_test, numeric_test, y_test):
    tfidf = model_bundle['tfidf']
    clf   = model_bundle['clf']

    X_text    = tfidf.transform(text_test)
    X_numeric = csr_matrix(numeric_test.values.astype(float))
    X_combined = hstack([X_text, X_numeric])

    y_pred  = clf.predict(X_combined)
    y_proba = clf.predict_proba(X_combined)

    acc = accuracy_score(y_test, y_pred)
    print("\n" + "="*50)
    print(f"ACCURACY : {acc*100:.2f}%")
    print("="*50)
    print(classification_report(y_test, y_pred, target_names=['Real', 'Fake']))

    cm = confusion_matrix(y_test, y_pred)
    print("CONFUSION MATRIX:")
    print(f"  True Real   (correct) : {cm[0][0]}")
    print(f"  True Fake   (correct) : {cm[1][1]}")
    print(f"  False Fake  (wrong)   : {cm[0][1]}")
    print(f"  Missed Fakes (wrong)  : {cm[1][0]}")

    # Feature importance — top numeric features
    tfidf_size = len(tfidf.vocabulary_)
    numeric_cols = model_bundle['numeric_columns']
    importances = clf.feature_importances_
    numeric_importances = importances[tfidf_size:]
    print("\nTop numeric feature importances:")
    for col, imp in sorted(zip(numeric_cols, numeric_importances), key=lambda x: -x[1]):
        print(f"  {col:<30} {imp:.4f}")

    return acc


# ── Save / Load ───────────────────────────────────────────────────────────────

def save_model(model_bundle):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model_bundle, MODEL_PATH)
    size = os.path.getsize(MODEL_PATH) / 1024
    print(f"\nModel saved → {MODEL_PATH} ({size:.1f} KB)")


# ── Single-item prediction helper ─────────────────────────────────────────────

def predict_sample(model_bundle,
                   title='', company='', description='',
                   requirements='', benefits='',
                   telecommuting=0, has_company_logo=1, has_questions=0):

    tfidf = model_bundle['tfidf']
    clf   = model_bundle['clf']

    # Text
    text = clean_text(f"{title} {company} {description} {requirements} {benefits}")
    X_text = tfidf.transform([text])

    # Build a fake single-row DataFrame to reuse engineer_features
    row = pd.DataFrame([{
        'title': title,
        'company_profile': company,
        'description': description,
        'requirements': requirements,
        'benefits': benefits,
        'telecommuting': telecommuting,
        'has_company_logo': has_company_logo,
        'has_questions': has_questions,
        'salary_range': np.nan,
        'department': np.nan,
    }])
    numeric = engineer_features(row)
    X_numeric = csr_matrix(numeric.values.astype(float))

    X_combined = hstack([X_text, X_numeric])

    pred  = clf.predict(X_combined)[0]
    proba = clf.predict_proba(X_combined)[0]
    conf  = proba[1] if pred == 1 else proba[0]
    label = "FAKE" if pred == 1 else "REAL"
    print(f"  [{label}] {title[:60]} — {conf*100:.1f}% confidence")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    df = load_data()
    text_X, numeric_X, y = build_features(df)

    (text_train, text_test,
     num_train,  num_test,
     y_train,    y_test) = train_test_split(
        text_X, numeric_X, y,
        test_size=0.2, random_state=42, stratify=y
    )

    model_bundle = train(text_train, num_train, y_train)
    evaluate(model_bundle, text_test, num_test, y_test)
    save_model(model_bundle)

    print("\nSample predictions:")

    # Should be FAKE
    predict_sample(model_bundle,
        title="Data Entry Work From Home",
        company="Global Solutions",
        description="No experience needed earn 5000 weekly immediate start no background check",
        requirements="No qualifications needed",
        telecommuting=1,
        has_company_logo=0,
        has_questions=0
    )

    # Should be REAL
    predict_sample(model_bundle,
        title="Frontend Engineer React",
        company="Stripe",
        description="Build payment UI features used by millions collaborate with product and design",
        requirements="3 years React TypeScript testing frameworks",
        telecommuting=0,
        has_company_logo=1,
        has_questions=1
    )

    print("\nDone! Your model is ready.")