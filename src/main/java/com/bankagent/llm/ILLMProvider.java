package com.bankagent.llm;

import dev.langchain4j.model.chat.ChatLanguageModel;

/**
 * Interface for providing the LLM model.
 * Follows Dependency Inversion Principle.
 */
public interface ILLMProvider {
    ChatLanguageModel getModel();
}
