package com.bankagent.core.exceptions;

public class AiGuardrailException extends AiAgentException {
    
    public AiGuardrailException(String message) {
        super(message, "AI_GUARDRAIL_ERROR");
    }

    public AiGuardrailException(String message, Throwable cause) {
        super(message, cause, "AI_GUARDRAIL_ERROR");
    }
}
