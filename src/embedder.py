from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

class ResumeJobEmbedder:
    """Handles embedding generation using Sentence Transformers"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedder with a pre-trained model
        
        Some models that can switch to:
        - 'jinaai/jina-embeddings-v2-base-en': tuned for semantic retrieval and job matching
        - 'BAAI/bge-base-en-v1.5': strong for general English text understanding
        - 'all-MiniLM-L6-v2': fast baseline
        - 'all-mpnet-base-v2': more accurate but slower
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def encode_text(self, text: Union[str, List[str]], show_progress: bool = True) -> np.ndarray:
        """
        Encode text into embeddings.
        Works for single strings or lists of strings.
        """
        if isinstance(text, str):
            text = [text]

        embeddings = self.model.encode(
            text,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # makes cosine similarity more stable
        )
        return embeddings

    def encode_resume(self, resume_text: str) -> np.ndarray:
        """Encode a single resume"""
        return self.encode_text(resume_text, show_progress=False)

    def encode_jobs(self, job_texts: List[str]) -> np.ndarray:
        """Encode multiple job descriptions"""
        return self.encode_text(job_texts, show_progress=True)
