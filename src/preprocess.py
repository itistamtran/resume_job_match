import pandas as pd
import re
import string
from typing import List

class TextPreprocessor:
    """Handles text preprocessing for resumes and job descriptions"""
    
    def __init__(self):
        self.stopwords = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        ])
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def remove_stopwords(self, text: str) -> str:
        """Remove common stopwords"""
        words = text.split()
        filtered_words = [w for w in words if w not in self.stopwords and len(w) > 2]
        return ' '.join(filtered_words)
    
    def preprocess(self, text: str, remove_stops: bool = True) -> str:
        """Full preprocessing pipeline"""
        text = self.clean_text(text)
        if remove_stops:
            text = self.remove_stopwords(text)
        return text


def load_and_preprocess_data(csv_path: str) -> pd.DataFrame:
    """Load and preprocess job descriptions from CSV"""
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} job descriptions")
    print(f"Columns: {df.columns.tolist()}")
    
    # Initialize preprocessor
    preprocessor = TextPreprocessor()
    
    # Identify text columns (adjust based on your CSV structure)
    text_columns = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['description', 'title', 'requirement', 'text']):
            text_columns.append(col)
    
    # Combine relevant text columns
    if text_columns:
        df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)
    else:
        # Fallback: use all text columns
        df['combined_text'] = df.fillna('').agg(' '.join, axis=1)
    
    # Preprocess
    print("Preprocessing text...")
    df['processed_text'] = df['combined_text'].apply(preprocessor.preprocess)
    
    return df