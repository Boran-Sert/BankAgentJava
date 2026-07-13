package com.bankagent.vectordb;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.store.embedding.EmbeddingStore;

public interface IVectorDbService {
    EmbeddingStore<TextSegment> getEmbeddingStore();
    void saveSkill(String skillName, String skillDescription);
}
