from pathlib import Path
import pickle

LABEL_TO_CATEGORY = {'DP-1':'Misdirection','DP-2':'Hidden Costs','DP-3':'Confirmshaming','DP-4':'Disguised Ads','DP-5':'Forced Continuity','DP-6':'Urgency / Scarcity'}
MODEL_PATH = Path(__file__).parent.parent / 'data' / 'models' / 'classifier.pkl'
CONFIDENCE_THRESHOLD = 0.55

class DarkPatternClassifier:
    def __init__(self):
        self.pipeline = None; self._available = False; self._load()
    def _load(self):
        if MODEL_PATH.exists():
            with open(MODEL_PATH,'rb') as f: self.pipeline = pickle.load(f); self._available = True
            print(f"[classifier] Loaded model from {MODEL_PATH}")
        else:
            print(f"[classifier] No trained model found at {MODEL_PATH}.")
    @property
    def available(self): return self._available
    def predict(self, texts):
        if not self._available or not texts: return []
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            probs = self.pipeline.predict_proba(texts)
            labels = self.pipeline.classes_
        results = []
        for text, prob_row in zip(texts, probs):
            idx = prob_row.argmax()
            label = str(labels[idx])  # force plain str
            confidence = float(prob_row[idx])
            if label != 'NONE' and confidence >= CONFIDENCE_THRESHOLD:
                results.append({'text': str(text), 'label': label, 'category': LABEL_TO_CATEGORY.get(label, label), 'confidence': round(confidence, 3)})
        return results

_classifier = None
def get_classifier():
    global _classifier
    if _classifier is None: _classifier = DarkPatternClassifier()
    return _classifier
