import pandas as pd
import joblib
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from tqdm import tqdm


def train_and_compare_models(data_path="dataset.csv", model_save_path="best_model.pkl"):
    print("📦 Loading and preprocessing dataset...")
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["email", "type"])
    X = df["email"]
    y = df["type"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    base_vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))

    # Define model configs
    models = {
        "MultinomialNB": MultinomialNB(),
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "LinearSVC": LinearSVC(),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42)
    }

    best_model = None
    best_score = 0
    best_name = ""

    print("🚀 Training models...\n")
    for name in tqdm(models, desc="Model Training"):
        model = models[name]
        pipeline = Pipeline([
            ('tfidf', base_vectorizer),
            ('clf', model)
        ])

        start_time = time.time()
        pipeline.fit(X_train, y_train)
        train_time = time.time() - start_time

        y_pred = pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)
        macro_f1 = report["macro avg"]["f1-score"]

        print(f"\n📊 {name} — F1 Score: {macro_f1:.4f} | Training Time: {train_time:.2f}s")
        print(classification_report(y_test, y_pred))

        if macro_f1 > best_score:
            best_model = pipeline
            best_score = macro_f1
            best_name = name

    # Optional: tune LinearSVC with GridSearch
    print("\n🎯 Hyperparameter tuning for LinearSVC...")
    svc_pipeline = Pipeline([
        ('tfidf', base_vectorizer),
        ('clf', LinearSVC())
    ])

    param_grid = {
        'clf__C': [0.01, 0.1, 1, 10],
        'tfidf__ngram_range': [(1,1), (1,2)]
    }

    grid = GridSearchCV(svc_pipeline, param_grid, cv=3, scoring='f1_macro', n_jobs=-1)
    grid.fit(X_train, y_train)

    y_pred = grid.predict(X_test)
    tuned_f1 = f1_score(y_test, y_pred, average='macro')
    print(f"\n🔧 Tuned LinearSVC — F1 Score: {tuned_f1:.4f}")
    print(classification_report(y_test, y_pred))

    if tuned_f1 > best_score:
        best_model = grid.best_estimator_
        best_score = tuned_f1
        best_name = "Tuned LinearSVC"

    # Save best model
    joblib.dump(best_model, model_save_path)
    print(f"\n✅ Best model: {best_name} (F1 Score: {best_score:.4f})")
    print(f"💾 Model saved to {model_save_path}")


def predict_category(email_text, model_path="best_model.pkl", return_confidence=False):
    model = joblib.load(model_path)
    label = model.predict([email_text])[0]

    if return_confidence:
        if hasattr(model.named_steps['clf'], 'decision_function'):
            decision = model.decision_function([email_text])
            confidence = max(decision[0])  # not normalized
            return label, confidence
        else:
            return label, None

    return label