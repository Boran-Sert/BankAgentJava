package com.bankagent.core.exceptions;

public class AiAgentException extends RuntimeException {
    
    private final String errorCode;

    public AiAgentException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    public AiAgentException(String message, Throwable cause, String errorCode) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}
