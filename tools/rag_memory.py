import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

class RAGMemory:
    """Gestionnaire de mémoire vectorielle (RAG) avec FAISS et SentenceTransformers"""
    
    def __init__(self, storage_dir=".nemesis_memory"):
        self.storage_dir = Path(storage_dir)
        self.index_file = self.storage_dir / "vector.index"
        self.metadata_file = self.storage_dir / "metadata.json"
        
        # Création du dossier de stockage si nécessaire
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Chargement du modèle d'embedding (léger et multilingue)
        print("📥 Chargement du modèle d'embedding (peut prendre un moment)...")
        self.embedding_dim = 384
        self.model = None
        
        try:
            # 1. Tentative hors-ligne (rapide et sûr si déjà téléchargé)
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', local_files_only=True)
            # print("✅ Modèle RAG chargé (cache local).")
        except Exception:
            # 2. Tentative en ligne (si pas dans le cache)
            try:
                print("⚠️ Modèle non trouvé localement, tentative de téléchargement...")
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception as e:
                print(f"❌ ERREUR CRITIQUE RAG: Impossible de charger le modèle d'embedding.")
                print(f"   Détail: {e}")
                print("   💡 Le système RAG sera désactivé pour cette session.")
                self.model = None
        
        # Chargement ou création de l'index FAISS
        self.index = None
        self.metadata = []
        self.load()

    def load(self):
        """Charge l'index et les métadonnées depuis le disque"""
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                print(f"✅ RAG: {len(self.metadata)} documents chargés.")
            except Exception as e:
                print(f"⚠️ Erreur chargement RAG: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Crée un nouvel index vide"""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.metadata = []
        print("🆕 RAG: Nouvel index créé.")

    def save(self):
        """Sauvegarde l'index et les métadonnées sur le disque"""
        if self.index:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            # print("💾 RAG: Index sauvegardé.")

    def add_text(self, text, source="unknown", type="text"):
        """Ajoute un texte à la mémoire vectorielle"""
        if not text.strip():
            return
            
        # Découpage basique en chunks (par paragraphes ou taille fixe si très long)
        # Ici on fait simple: on coupe par paragraphes
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        
        if not chunks:
            return

        if not self.model:
             print("⚠️ RAG désactivé (modèle non chargé).")
             return

        embeddings = self.model.encode(chunks)
        self.index.add(np.array(embeddings).astype("float32"))
        
        for chunk in chunks:
            self.metadata.append({
                "content": chunk,
                "source": source,
                "type": type,
                "timestamp": self._get_timestamp()
            })
            
        self.save()
        print(f"➕ RAG: {len(chunks)} chunks ajoutés depuis {source}.")

    def search(self, query, k=3):
        """Recherche les passages les plus pertinents pour une requête"""
        if self.index.ntotal == 0:
            return []
            
        if not self.model:
            return []

        query_vector = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_vector).astype("float32"), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                item = self.metadata[idx]
                results.append({
                    "content": item["content"],
                    "source": item["source"],
                    "score": float(distances[0][i])
                })
        
        return results

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
