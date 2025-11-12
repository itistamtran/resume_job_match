import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
from src.explanation import explain_match

class JobRecommender:
    """Recommends jobs based on resume similarity"""
    
    def __init__(self, job_embeddings: np.ndarray, job_data: pd.DataFrame):
        """
        Initialize recommender with pre-computed job embeddings
        
        Args:
            job_embeddings: Numpy array of job embeddings
            job_data: DataFrame with job information
        """
        self.job_embeddings = job_embeddings
        self.job_data = job_data.reset_index(drop=True)
        
    def find_similar_jobs(self, resume_embedding: np.ndarray, 
                         top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Find most similar jobs to the resume
        
        Args:
            resume_embedding: Embedding vector for the resume
            top_k: Number of top matches to return
            
        Returns:
            List of (job_index, similarity_score) tuples
        """
        # Reshape 
        if resume_embedding.ndim == 1:
            resume_embedding = resume_embedding.reshape(1, -1)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(resume_embedding, self.job_embeddings)[0]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return indices and scores
        results = [(idx, similarities[idx]) for idx in top_indices]
        
        return results
    
    def recommend(self, resume_text: str, embedder, 
                  top_k: int = 50) -> pd.DataFrame:
        """
        Get job recommendations for a resume
        
        Args:
            resume_text: Raw or processed resume text
            embedder: ResumeJobEmbedder instance
            top_k: Number of recommendations
            
        Returns:
            DataFrame with recommended jobs and similarity scores
        """
        # Encode resume
        print("Encoding resume...")
        resume_embedding = embedder.encode_resume(resume_text)
        
        # Find similar jobs
        print(f"Finding top {top_k} matches...")
        matches = self.find_similar_jobs(resume_embedding, top_k)
        
        # Prepare results
        results = []
        for idx, score in matches:
            job_info = self.job_data.iloc[idx].to_dict()
            job_info['similarity_score'] = score
            job_info['match_percentage'] = round(score * 100, 2)
            results.append(job_info)
        
        results_df = pd.DataFrame(results)
        
        return results_df
    
    def explain_top_match(self, resume_text: str, embedder, top_k: int = 1):
        """
        Provide an explanation for the top matched job (shared and missing skills).
        """
        results_df = self.recommend(resume_text, embedder, top_k=top_k)
        top_job = results_df.iloc[0]
        job_idx = int(top_job["index"]) if "index" in results_df.columns else results_df.index[0]
        job_text = self.job_data.iloc[job_idx]["clean_job"]


        explanation = explain_match(resume_text, job_text)
        return {
            "job_title": top_job.get("title", "Unknown Job"),
            "similarity_score": top_job["similarity_score"],
            "shared_skills": explanation["shared_skills"],
            "missing_skills": explanation["missing_skills"],
            "extra_skills": explanation["extra_skills"]
        }
    