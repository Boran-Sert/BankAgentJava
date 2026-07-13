package com.bankagent.workflow;

import com.bankagent.core.contracts.BaseResponse;
import com.bankagent.llm.ILLMProvider;
import com.bankagent.skills.BankingSkills;
import com.bankagent.guardrails.GuardrailsService;
import com.bankagent.vectordb.ChromaDbService;
import dev.langchain4j.memory.chat.ChatMemoryProvider;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.rag.content.retriever.EmbeddingStoreContentRetriever;
import dev.langchain4j.rag.DefaultRetrievalAugmentor;
import dev.langchain4j.rag.RetrievalAugmentor;
import dev.langchain4j.service.AiServices;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;

@Service
public class AgentWorkflowService {

    private static final Logger log = LoggerFactory.getLogger(AgentWorkflowService.class);

    private final ILLMProvider llmProvider;
    private final BankingSkills bankingSkills;
    private final GuardrailsService guardrailsService;
    private final ChromaDbService chromaDbService;
    
    private IBankingAgent agent;

    public AgentWorkflowService(ILLMProvider llmProvider, BankingSkills bankingSkills, GuardrailsService guardrailsService, ChromaDbService chromaDbService) {
        this.llmProvider = llmProvider;
        this.bankingSkills = bankingSkills;
        this.guardrailsService = guardrailsService;
        this.chromaDbService = chromaDbService;
    }

    @PostConstruct
    public void init() {
        RetrievalAugmentor augmentor = null;
        if (chromaDbService.getEmbeddingStore() != null && chromaDbService.getEmbeddingModel() != null) {
            EmbeddingStoreContentRetriever contentRetriever = EmbeddingStoreContentRetriever.builder()
                .embeddingStore(chromaDbService.getEmbeddingStore())
                .embeddingModel(chromaDbService.getEmbeddingModel())
                .maxResults(3)
                .minScore(0.6)
                .build();
                
            augmentor = DefaultRetrievalAugmentor.builder()
                .contentRetriever(contentRetriever)
                .build();
        }

        ChatMemoryProvider chatMemoryProvider = memoryId -> MessageWindowChatMemory.withMaxMessages(20);

        var builder = AiServices.builder(IBankingAgent.class)
                .chatLanguageModel(llmProvider.getModel())
                .chatMemoryProvider(chatMemoryProvider)
                .tools(bankingSkills);
                
        if (augmentor != null) {
            builder.retrievalAugmentor(augmentor);
        }
        
        this.agent = builder.build();
    }

    public BaseResponse processUserMessage(String sessionId, String userMessage) {
        log.info("Processing user message for session {}: {}", sessionId, userMessage);
        
        guardrailsService.validateInput(userMessage);
        
        String aiResponse = agent.chat(sessionId, userMessage);
        
        String safeResponse = guardrailsService.sanitizeOutput(aiResponse);
        
        BaseResponse response = new BaseResponse();
        response.setAgent("JavaBankingAgent");
        response.setIntent("Auto-Detected");
        response.setStatus("COMPLETED");
        response.setMessageToUser(safeResponse);
        
        return response;
    }
}
