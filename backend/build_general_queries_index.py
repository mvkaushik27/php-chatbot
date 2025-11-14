"""
Build FAISS Index for General Library Queries
==============================================
This script creates a semantic search index for general_queries.json
using FAISS and sentence-transformers.

Run once to build index:
    python build_general_queries_index.py

Outputs:
    - general_queries_index.faiss (vector index)
    - general_queries_mapping.pkl (question->answer mapping)
"""

import json
import pickle
import numpy as np
from pathlib import Path

def build_general_queries_index():
    """
    Build FAISS index from general_queries.json for semantic search.
    Creates index and mapping files for fast similarity search.
    """
    
    BASE_DIR = Path(__file__).parent
    GENERAL_QUERIES_FILE = BASE_DIR / "general_queries.json"
    INDEX_OUTPUT = BASE_DIR / "general_queries_index.faiss"
    MAPPING_OUTPUT = BASE_DIR / "general_queries_mapping.pkl"
    MODEL_PATH = BASE_DIR / "models" / "all-MiniLM-L6-v2"
    
    print("=" * 60)
    print("Building FAISS Index for General Library Queries")
    print("=" * 60)
    
    # Check if files exist
    if not GENERAL_QUERIES_FILE.exists():
        print(f"ERROR: {GENERAL_QUERIES_FILE} not found!")
        return False
    
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("   Please ensure sentence-transformer model is downloaded.")
        return False
    
    # Load general queries
    print(f"\nLoading general queries from: {GENERAL_QUERIES_FILE.name}")
    with open(GENERAL_QUERIES_FILE, 'r', encoding='utf-8') as f:
        general_queries = json.load(f)
    
    print(f"SUCCESS: Loaded {len(general_queries)} Q&A pairs")
    
    # Prepare data
    questions = list(general_queries.keys())
    answers = []
    
    print("\nProcessing Q&A pairs...")
    for question in questions:
        answer_data = general_queries[question]
        if isinstance(answer_data, dict):
            answers.append(answer_data)
        else:
            # Parse string to dict if needed
            try:
                answers.append(json.loads(answer_data.replace("'", '"')))
            except:
                # Fallback: create simple dict
                answers.append({"answer": str(answer_data), "intent": "general"})
    
    # Import heavy dependencies only when needed
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"ERROR: Missing required package: {e}")
        print("   Install with: pip install faiss-cpu sentence-transformers")
        return False
    
    # Load model
    print(f"\nLoading sentence transformer model from: {MODEL_PATH.name}")
    model = SentenceTransformer(str(MODEL_PATH))
    print("SUCCESS: Model loaded successfully")
    
    # Encode questions
    print(f"\nEncoding {len(questions)} questions into embeddings...")
    embeddings = model.encode(questions, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype('float32')
    
    print(f"SUCCESS: Generated embeddings (shape: {embeddings.shape})")
    
    # Build FAISS index
    print("\nBuilding FAISS index...")
    dimension = embeddings.shape[1]  # Should be 384 for all-MiniLM-L6-v2
    print(f"   Dimension: {dimension}")
    
    # Use L2 distance (Euclidean) - works well for normalized embeddings
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"SUCCESS: FAISS index built with {index.ntotal} vectors")
    
    # Save index
    print(f"\nSaving FAISS index to: {INDEX_OUTPUT.name}")
    faiss.write_index(index, str(INDEX_OUTPUT))
    print(f"   Size: {INDEX_OUTPUT.stat().st_size / 1024:.2f} KB")
    
    # Create mapping (index -> answer data)
    print(f"\nCreating mapping file...")
    mapping = []
    for i, question in enumerate(questions):
        mapping.append({
            "question": question,
            "answer_data": answers[i],
            "index": i
        })
    
    with open(MAPPING_OUTPUT, 'wb') as f:
        pickle.dump(mapping, f)
    
    print(f"Saved mapping to: {MAPPING_OUTPUT.name}")
    print(f"   Size: {MAPPING_OUTPUT.stat().st_size / 1024:.2f} KB")
    
    # Test the index
    print("\n" + "=" * 60)
    print("Testing Index with Sample Queries")
    print("=" * 60)
    
    test_queries = [
        "what time library open",
        "how to borrow books",
        "fine for late return",
        "access online journals",
        "library contact number"
    ]
    
    for test_query in test_queries:
        print(f"\nQuery: '{test_query}'")
        test_embedding = model.encode([test_query])
        distances, indices = index.search(test_embedding, k=3)
        
        # Convert L2 distance to similarity percentage
        similarities = [1 / (1 + dist) for dist in distances[0]]
        
        print("   Top 3 matches:")
        for i, (sim, idx) in enumerate(zip(similarities, indices[0]), 1):
            match = mapping[idx]
            print(f"   {i}. [{sim*100:.1f}%] {match['question'][:60]}")
    
    print("\n" + "=" * 60)
    print("SUCCESS: FAISS Index Build Complete!")
    print("=" * 60)
    print("\nGenerated Files:")
    print(f"   * {INDEX_OUTPUT.name}")
    print(f"   * {MAPPING_OUTPUT.name}")
    print("\nReady to use FAISS semantic search for general queries!")
    
    return True


if __name__ == "__main__":
    try:
        success = build_general_queries_index()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
