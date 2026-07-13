package com.bankagent.vectordb;

import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.embedding.onnx.allminilml6v2q.AllMiniLmL6V2QuantizedEmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.chroma.ChromaEmbeddingStore;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;

@Service
public class ChromaDbService implements IVectorDbService {

    private static final Logger log = LoggerFactory.getLogger(ChromaDbService.class);

    private EmbeddingStore<TextSegment> embeddingStore;
    private EmbeddingModel embeddingModel;

    @Value("${app.chroma.base-url:http://localhost:8000}")
    private String chromaBaseUrl;

    @Value("${app.chroma.collection-name:banking_skills}")
    private String collectionName;

    @PostConstruct
    public void init() {
        try {
            // Using local embedded quantization model for semantic search
            this.embeddingModel = new AllMiniLmL6V2QuantizedEmbeddingModel();
            
            this.embeddingStore = ChromaEmbeddingStore.builder()
                    .baseUrl(chromaBaseUrl)
                    .collectionName(collectionName)
                    .build();
            log.info("ChromaDB initialized at {}", chromaBaseUrl);
        } catch (Exception e) {
            log.warn("ChromaDB connection failed. Please ensure Chroma is running. Fallback to in-memory could be added here.", e);
        }
    }

    @Override
    public EmbeddingStore<TextSegment> getEmbeddingStore() {
        return this.embeddingStore;
    }

    @Override
    public void saveSkill(String skillName, String skillDescription) {
        if (embeddingStore == null) return;
        
        TextSegment segment = TextSegment.from(skillDescription, Metadata.metadata("name", skillName));
        Embedding embedding = embeddingModel.embed(segment).content();
        
        embeddingStore.add(embedding, segment);
        log.info("Saved skill to ChromaDB: {}", skillName);
    }
    
    public EmbeddingModel getEmbeddingModel() {
        return this.embeddingModel;
    }
}
