package com.bankagent.llm;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.ollama.OllamaChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * Implementation for connecting natively to local Ollama.
 * Langchain4j's Ollama provider supports native Tool Calling automatically.
 */
@Service
@ConditionalOnProperty(name = "app.llm.provider", havingValue = "ollama", matchIfMissing = true)
public class OllamaLLMProvider implements ILLMProvider {

    private final ChatLanguageModel chatModel;

    public OllamaLLMProvider(
            @Value("${langchain4j.ollama.chat-model.base-url:http://localhost:11434}") String baseUrl,
            @Value("${langchain4j.ollama.chat-model.model-name:llama3}") String modelName,
            @Value("${langchain4j.ollama.chat-model.temperature:0.0}") double temperature) {

        // OllamaChatModel natively understands JSON schemas and Tool Calling starting from LC4j 0.3x
        this.chatModel = OllamaChatModel.builder()
                .baseUrl(baseUrl)
                .modelName(modelName)
                .temperature(temperature)
                .timeout(Duration.ofSeconds(120)) // Local LLMs might take time to generate
                .build();
    }

    @Override
    public ChatLanguageModel getModel() {
        return chatModel;
    }
}
