package com.bankagent.llm;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.ChatMessage;
import dev.langchain4j.model.output.Response;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import java.util.List;

/**
 * Implementation for connecting to a local/embedded LLM model directly via Java code.
 * (e.g. DeepLearning4j, local ONNX model, or custom Java bindings)
 * Other developers can implement the getModel() logic here.
 */
@Service
@ConditionalOnProperty(name = "app.use-embedded-llm", havingValue = "true")
public class EmbeddedLLMProvider implements ILLMProvider {

    @Override
    public ChatLanguageModel getModel() {
        return new ChatLanguageModel() {
            @Override
            public String generate(String userMessage) {
                throw new UnsupportedOperationException("Embedded model not yet implemented.");
            }

            @Override
            public Response<AiMessage> generate(List<ChatMessage> messages) {
                throw new UnsupportedOperationException("Embedded model not yet implemented.");
            }
        };
    }
}
