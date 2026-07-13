package com.bankagent.api;

import com.bankagent.core.contracts.BaseResponse;
import com.bankagent.workflow.AgentWorkflowService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/agent")
public class AgentController {

    private final AgentWorkflowService agentWorkflowService;

    public AgentController(AgentWorkflowService agentWorkflowService) {
        this.agentWorkflowService = agentWorkflowService;
    }

    @PostMapping("/chat")
    public ResponseEntity<BaseResponse> chat(@Valid @RequestBody ChatRequest request) {
        BaseResponse response = agentWorkflowService.processUserMessage(request.getSessionId(), request.getMessage());
        return ResponseEntity.ok(response);
    }

    public static class ChatRequest {
        @NotBlank(message = "Message cannot be blank")
        private String message;
        
        @NotBlank(message = "Session ID is required")
        private String sessionId; // Mandatory for multi-turn conversations

        public ChatRequest() {}

        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }

        public String getSessionId() { return sessionId; }
        public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    }
}
