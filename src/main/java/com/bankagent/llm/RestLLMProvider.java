package com.bankagent.llm;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * Implementation for connecting to external or local HTTP REST LLMs (like GPT-OSS via OpenAI API spec).
 */
@Service
@ConditionalOnProperty(name = "app.llm.provider", havingValue = "openai")
public class RestLLMProvider implements ILLMProvider {

    private final ChatLanguageModel chatModel;

    public RestLLMProvider(
            @Value("${langchain4j.open-ai.chat-model.base-url}") String baseUrl,
            @Value("${langchain4j.open-ai.chat-model.api-key}") String apiKey,
            @Value("${langchain4j.open-ai.chat-model.model-name}") String modelName,
            @Value("${langchain4j.open-ai.chat-model.temperature:0.0}") double temperature) {

        this.chatModel = OpenAiChatModel.builder()
                .baseUrl(baseUrl)
                .apiKey(apiKey)
                .modelName(modelName)
                .temperature(temperature)
                .timeout(Duration.ofSeconds(60))
                .build();
    }

    @Override
    public ChatLanguageModel getModel() {
        return chatModel;
    }
}
