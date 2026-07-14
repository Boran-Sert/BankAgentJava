/**
 * Ajanların dış dünyayla bağlantılı araçları (tools) çalıştırırken karşılaştığı veri veya sistem hatalarıdır.
 */
package com.bankagent.core.exceptions;

public class AiSkillExecutionException extends AiAgentException {
    
    public AiSkillExecutionException(String message) {
        super(message, "AI_SKILL_EXECUTION_ERROR");
    }

    public AiSkillExecutionException(String message, Throwable cause) {
        super(message, cause, "AI_SKILL_EXECUTION_ERROR");
    }
}
