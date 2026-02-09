import sys
import os

try:
    print("Checking imports...")
    import torch
    print(f"✅ Torch: {torch.__version__} (CUDA available: {torch.cuda.is_available()})")
    
    import numpy
    print(f"✅ Numpy: {numpy.__version__}")
    
    import faiss
    print(f"✅ Faiss: {faiss.__version__}")
    
    from sentence_transformers import SentenceTransformer
    print("✅ SentenceTransformers imported. Loading model...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("✅ Model loaded.")
    
    embeddings = model.encode(["Ceci est un test."])
    print(f"✅ Embedding shape: {embeddings.shape}")
    
    print("🎉 RAG Dependencies validated!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
