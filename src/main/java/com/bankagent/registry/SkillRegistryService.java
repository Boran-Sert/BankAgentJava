/**
 * Sistemdeki tüm BankingSkills araçlarını bellekte (memory) ve veritabanında kayda alarak erişime açar.
 */
package com.bankagent.registry;

import com.bankagent.core.exceptions.AiAgentException;
import com.bankagent.vectordb.IVectorDbService;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import dev.langchain4j.store.embedding.EmbeddingSearchRequest;
import dev.langchain4j.store.embedding.EmbeddingSearchResult;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.data.embedding.Embedding;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class SkillRegistryService {

    private static final Logger log = LoggerFactory.getLogger(SkillRegistryService.class);
    private final IVectorDbService vectorDbService;

    public SkillRegistryService(IVectorDbService vectorDbService) {
        this.vectorDbService = vectorDbService;
    }

    /**
     * Registers a new skill directly into ChromaDB.
     */
    public void registerSkill(String name, String description) {
        vectorDbService.saveSkill(name, description);
        log.info("Skill registered: {}", name);
    }

    /**
     * Searches for relevant skills based on user intent.
     */
    public List<String> findRelevantSkills(String userIntent, EmbeddingModel embeddingModel, int maxResults) {
        if (vectorDbService.getEmbeddingStore() == null) {
            throw new AiAgentException("Vector DB not initialized.", "VECTOR_DB_ERROR");
        }

        try {
            Embedding intentEmbedding = embeddingModel.embed(userIntent).content();
            
            EmbeddingSearchRequest searchRequest = EmbeddingSearchRequest.builder()
                    .queryEmbedding(intentEmbedding)
                    .maxResults(maxResults)
                    .minScore(0.6)
                    .build();

            EmbeddingSearchResult<TextSegment> searchResult = vectorDbService.getEmbeddingStore().search(searchRequest);
            
            List<String> relevantSkills = searchResult.matches().stream()
                .map(match -> match.embedded().metadata().getString("name") + ": " + match.embedded().text())
                .collect(Collectors.toList());
                
            log.info("Found {} relevant skills for intent: {}", relevantSkills.size(), userIntent);
            return relevantSkills;
        } catch (Exception e) {
            log.error("Failed to search skills.", e);
            throw new AiAgentException("Skill search failed: " + e.getMessage(), e, "SKILL_SEARCH_ERROR");
        }
    }
}
