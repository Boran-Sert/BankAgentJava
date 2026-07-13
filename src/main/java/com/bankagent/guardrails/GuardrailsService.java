package com.bankagent.guardrails;

import com.bankagent.core.exceptions.AiGuardrailException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.regex.Pattern;

@Service
public class GuardrailsService {

    private static final Logger log = LoggerFactory.getLogger(GuardrailsService.class);
    private static final Pattern CREDIT_CARD_PATTERN = Pattern.compile("\\b(?:\\d[ -]*?){13,16}\\b");

    /**
     * Validates user input before it goes to the LLM.
     * Blocks malicious prompts, prompt injections, or unauthorized requests.
     */
    public void validateInput(String userInput) {
        if (userInput == null || userInput.isBlank()) {
            throw new AiGuardrailException("Kullanıcı girdisi boş olamaz.");
        }
        
        String lowerInput = userInput.toLowerCase();
        if (lowerInput.contains("ignore previous instructions") || lowerInput.contains("system prompt")) {
            log.warn("Blocked potential prompt injection attack: {}", userInput);
            throw new AiGuardrailException("Sistem güvenlik politikası ihlali tespit edildi.");
        }
    }

    /**
     * Validates LLM output before it goes to the user.
     * Ensures sensitive data (like full credit card numbers) is masked if the LLM leaked it.
     */
    public String sanitizeOutput(String llmOutput) {
        if (llmOutput == null) return "";
        
        String sanitized = CREDIT_CARD_PATTERN.matcher(llmOutput).replaceAll("**** **** **** ****");
        if (!sanitized.equals(llmOutput)) {
            log.info("Sanitized sensitive data from LLM output.");
        }
        
        return sanitized;
    }
}
