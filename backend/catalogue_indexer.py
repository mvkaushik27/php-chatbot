
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
from pathlib import Path

def build_catalogue_index(progress_callback=None):
    """
    Build FAISS index with progress updates
    Args:
        progress_callback: Optional function to receive progress updates
    """
    def update_progress(message, percentage=None):
        if progress_callback:
            progress_callback({"message": message, "percentage": percentage})
    
    # Load the catalogue
    update_progress("Loading catalogue...", 0)
    catalogue_df = pd.read_csv('catalogue.csv')
    total_rows = len(catalogue_df)
    
    # Initialize the sentence transformer
    update_progress("Initializing sentence transformer...", 5)
    model = SentenceTransformer(str(Path(__file__).parent / "models" / "all-MiniLM-L6-v2"))
    
    # Create text representations for searching
    update_progress("Processing catalogue entries...", 10)
    catalogue_texts = []
    catalogue_metadata = []
    for idx, row in catalogue_df.iterrows():
        # Combined text for semantic search
        text = f"{row['title']} {row.get('subtitle', '')} {row['author']}"
        catalogue_texts.append(text)
        
        # Store metadata for display
        metadata = {
            'title': row['title'],
            'subtitle': row.get('subtitle', ''),
            'author': row['author'],
            'itemcallnumber': row.get('itemcallnumber', ''),
            'editionstatement': row.get('editionstatement', ''),
            'isbn': row.get('isbn', ''),
            'barcode': row.get('barcode', ''),
            'pages': row.get('pages', ''),
            'publishercode': row.get('publishercode', ''),
            'place': row.get('place', ''),
            'copyrightdate': row.get('copyrightdate', ''),
            'price': row.get('price', '')
        }
        catalogue_metadata.append(metadata)
        
        # Update progress every 100 rows
        if idx % 100 == 0:
            progress = 10 + (20 * idx / total_rows)
            update_progress(f"Processing catalogue entries ({idx}/{total_rows})...", progress)
    
    # Generate embeddings
    update_progress("Generating embeddings...", 30)
    embeddings = model.encode(catalogue_texts, show_progress_bar=True)
    
    # Convert to float32 (required by FAISS)
    embeddings = np.array([embedding for embedding in embeddings]).astype("float32")
    
    # Build FAISS index
    update_progress("Building FAISS index...", 70)
    embedding_size = embeddings.shape[1]  # Get the size of embeddings
    index = faiss.IndexFlatL2(embedding_size)  # Create the index
    index.add(embeddings)  # Add vectors to the index
    
    # Save the index and catalogue data
    update_progress("Saving index and metadata...", 90)
    faiss.write_index(index, "catalogue_index.faiss")
    
    # Save metadata and texts
    with open('catalogue_data.pkl', 'wb') as f:
        pickle.dump({
            'texts': catalogue_texts,
            'metadata': catalogue_metadata,
            'total_entries': total_rows
        }, f)
    
    update_progress("Catalogue indexing completed!", 100)
    return index, catalogue_texts, catalogue_metadata

def search_catalogue(query, index, catalogue_texts, catalogue_metadata, k=5):
    """
    Search the catalogue using FAISS index and return formatted results
    
    Args:
        query (str): Search query
        index: FAISS index
        catalogue_texts (list): List of combined text representations
        catalogue_metadata (list): List of metadata dictionaries
        k (int): Number of results to return
        
    Returns:
        list: Formatted search results with metadata
    """
    # Initialize the model
    model = SentenceTransformer(str(Path(__file__).parent / "models" / "all-MiniLM-L6-v2"))
    
    # Generate query embedding
    query_vector = model.encode([query])
    
    # Search the index
    distances, indices = index.search(query_vector.astype("float32"), k)
    
    # Get the results with metadata
    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # FAISS returns -1 for empty slots
            metadata = catalogue_metadata[idx]
            score = 1 / (1 + distances[0][i])  # Convert distance to similarity score
            
            # Format the result
            result = {
                'title': metadata['title'],
                'author': metadata['author'],
                'itemcallnumber': metadata.get('itemcallnumber', ''),
                'publishercode': metadata.get('publishercode', ''),
                'copyrightdate': metadata.get('copyrightdate', ''),
                'isbn': metadata.get('isbn', ''),
                'score': f"{score:.2f}",
                'text': catalogue_texts[idx]
            }
            results.append(result)
    
    return results

if __name__ == "__main__":
    print("Building catalogue FAISS index...")
    try:
        index, texts, metadata = build_catalogue_index()
        try:
            print(f"SUCCESS: Built FAISS index with {len(texts)} entries")
        except UnicodeEncodeError:
            print("SUCCESS: Built FAISS index (console encoding issue with special characters)")
        exit(0)  # Success
    except Exception as e:
        try:
            print(f"FAILED: Could not build FAISS index: {e}")
        except UnicodeEncodeError:
            print("FAILED: Could not build FAISS index (console encoding issue)")
        import traceback
        try:
            traceback.print_exc()
        except UnicodeEncodeError:
            print("Traceback printing failed due to console encoding")
        exit(1)  # Failure