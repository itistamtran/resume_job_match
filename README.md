# Resume-to-Job Match Recommendation System

This project uses **Sentence Transformers** to analyze the similarity between resumes and job descriptions.  
It converts text into embeddings, computes cosine similarity, and ranks top job matches with a clean **Streamlit** interface.

🌐 **Live App:** [resumejobmatch-ai.streamlit.app](https://resumejobmatch-ai.streamlit.app/)

---

## Features

- **Resume Parsing** – supports `.pdf`, `.docx` and `.txt` formats
- **Job Description Processing** – cleans and embeds job text for comparison
- **Semantic Matching** – computes similarity scores between resumes and jobs
- **Top Match Visualization** – displays best matches with match percentages
- **Interactive UI** – built using Streamlit for quick exploration

## Project Structure

```
resume_job_match/
├── app/
│   └── interface.py                # Streamlit web interface
│   └── description_toggle.py       # Toggle long job descriptions
│   └── formatter.py                # Job text formatter
│   └── progress_circle.py          # Circular progress visualization
├── data/
│   ├── Resume.csv                  # Resume dataset
│   └── full_jobs_data.csv          # Job descriptions database
│   └── cleaned_jobs_full.csv
│   └── cleaned_jobs_for_model.csv
│   └── cleaned_resumes_full.csv
│   └── cleaned_resumes_for_model.csv
│   └── job_embeddings.npy
│   └── resume_embeddings.npy
├── notebooks/
│   ├── 01_data_preprocessing.ipynb
│   └── 02_embedding_and_similarity.ipynb
├── src/
│   ├── __init__.py
│   ├── embedder.py           # Embedding generation
│   └── recommender.py        # Job recommendation logic
│   └── explanation.py        # Match explanation
├── requirements.txt
└── README.md
```

---

## Installation

1. **Clone this repository**

   ```bash
   git clone https://github.com/itistamtran/resume_job_match.git
   cd resume-job-match
   ```

2. **Create a virtual environment**

   ```bash
   conda create -n resumeapp4200 python=3.10
   conda activate resumeapp4200
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Running the Web Application**
   Launch the Streamlit interface:

```bash
streamlit run app/interface.py
```

---

## Features

- Semantic similarity using Sentence Transformers
- Clean, intuitive Streamlit interface
- Preprocessing pipeline for text normalization
- Cosine similarity ranking
- Top-K job recommendations
- Match percentage scoring
- Live job fetching via APIs (future)

---

## Technical Details

### Embedding Model

- Default: `all-MiniLM-L6-v2` (384 dimensions, fast)
- Alternative: `all-mpnet-base-v2` (768 dimensions, more accurate) (in the future)

### Similarity Metric

- Cosine similarity measures how closely a resume matches each job description.
- Both resume and job embeddings are normalized to unit vectors for consistency.

---

## Dataset

### Job Dataset

`full_jobs_data.csv` should include:
| Column | Description |
| ------------- | ---------------------------------- |
| `source` | Data source (Adzuna, usajobs) |
| `id` | Job ID |
| `title` | Job title |
| `company` | Company name |
| `location` | Job location |
| `description` | Job description text |
| `url` | Job posting link |
| `salary_min` | Minimum salary |
| `salary_max` | Maximum salary |
| `date_posted` | Date the job was posted |

The system will automatically detect and combine relevant text columns.

### Resume Dataset

The project uses the Resume Dataset [Kaggle](https://www.kaggle.com/datasets/pranavvenugo/resume-and-job-description) to generate resume embeddings. This dataset includes 2,240 real-world resume samples across various domains.

Each entry in `Resume.csv` contains:

| Column        | Description                                   |
| ------------- | --------------------------------------------- |
| `ID`          | Unique identifier for each resume entry       |
| `Resume_str`  | Resume content in plain-text format           |
| `Resume_html` | Original HTML-formatted version of the resume |
| `Category`    | Professional field or job category            |

---

### Notebooks

- 01_data_preprocessing.ipynb – Text cleaning, tokenization, and preparation
- 02_embedding_and_similarity.ipynb – Embedding generation, normalization, and cosine similarity computation
  - Saves embeddings as .npy for faster app loading

---

## Future Enhancements

1. Real-time job fetching from APIs (Adzuna, USAJobs, RemoteOK, etc.)
2. Fine-tuning embeddings on domain-specific data
3. Resume feedback and improvement suggestions
4. User feedback loop for improved recommendations

---

## License

This project is licensed under the MIT License.
You’re free to use, modify, and distribute it with proper attribution.
