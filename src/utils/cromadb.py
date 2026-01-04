import json
import os
import chromadb
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
load_dotenv()

class ExperienceDB:
    def __init__(self, persist_dir = 'experience_db',
                 embeddings = None,
                 base_collection='experiences'):
        self.persist_dir = persist_dir
        self.embeddings = embeddings
        self.base_collection = base_collection
        self.registry_path = os.path.join(persist_dir, 'registry.json')
        
        os.makedirs(persist_dir, exist_ok=True)
        
        
        self.current_dim = getattr(self.embeddings,
                                   'dimensions',
                                   1536)
        self.current_model = getattr(self.embeddings,
                                     "model",
                                     "unknown-model")
        
        self.registry = self._load_registry()
        self.collection_name = self._resolve_collection()
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.vectorstore = self._load_or_create_collection()
        self._register_collection()
        
    def _load_registry(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                
            except Exception:
                return []
            
        return []
    
    def _save_registry(self):
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
            
    
    def _register_collection(self):
        if not any(c['name'] == self.collection_name for c in self.registry):
            self.registry.append({
                'name': self.collection_name,
                'dim' : self.current_dim,
                'model' : self.current_model
            })
            
            self._save_registry()
            
    def _resolve_collection(self):
        for c in self.registry:
            if c['model'] == self.current_model and c['dim'] == self.current_dim:
                return c['name']
            
        safe_model_name = self.current_model.replace('-','_').replace('.','_')
        return f"{self.base_collection}_dim{self.current_dim}_model_{safe_model_name}"
    
    def _load_or_create_collection(self):
        collection_exists_in_registry = any(c['name'] == self.collection_name for c in self.registry)
        
        if collection_exists_in_registry:
            try:
                native_collection = self.client.get_collection(
                    name = self.collection_name
                )
                meta = native_collection.metadata
                
                if meta is None:
                    print('meta가 없습니다.')
                    
                    native_collection.modify(metadata = {'model' : self.current_model,
                                                         'dimension': self.current_dim})
                else:
                    stored_dim = meta.get('dimension')
                    if stored_dim and stored_dim != self.current_dim:
                        print('기존차원불일치')
                        self.collection_name = f"{self.base_collection}_dim{self.current_dim}_model_{self.current_model.replace('-','_')}_new"
                        return self._create_new_collection()
                    
            except Exception as e:
                self.collection_name = f"{self.base_collection}_dim{self.current_dim}_model_{self.current_model.replace('-','_')}_new"
                return self._create_new_collection()
        
        else:
            return self._create_new_collection()
        
        return Chroma(
            client = self.client,
            collection_name = self.collection_name,
            embedding_function = self.embeddings,
            persist_directory= self.persist_dir
        )
        
    def _create_new_collection(self):
        new_store = Chroma.from_texts(
            texts= ["[SYSTEM_INIT]"],
            embedding=self.embeddings,
            metadatas = [{"init":True}],
            collection_name = self.collection_name,
            persist_directory=self.persist_dir
        )
        
        new_store._collection.modify(metadata = {'model': self.current_model,
                                                  'dimension': self.current_dim})
        new_store.persist()
        return new_store
    
    
    def add_experience(self, text, metadata = None):
        self.vectorstore.add_texts([text], metadatas = [metadata or {}])
        self.vectorstore.persist()
        
    def query_experience(self, query, k=1):
        try:
            if self.vectorstore._collection.count() == 0:
                return ''
            
            results = self.vectorstore.similarity_search_with_score(
                query,
                k=k,
                filter = {'feedback':'y'}
            )
            
            if not results:
                return ''
            
            doc, score = results[0]
            content = doc.page_content
            meata = doc.metadata
            
            return f"과거 작업 로그 {content}"
        
        except Exception as e:
            return ""
        
    def list_collections(self):
        return [f"{c['name']} ({c['model']}) ({c['dim']})" for c in self.registry]
    
    # def reembed_from(self, old_collection_name):
    #     pass