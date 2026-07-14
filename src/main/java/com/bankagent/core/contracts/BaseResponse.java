/**
 * Ajanların ve sistemin dışarıya döndüğü cevapları standart bir API formatına oturtan veri modelidir.
 */
package com.bankagent.core.contracts;

import java.util.Map;

public class BaseResponse {
    private String agent;
    private String intent;
    private String status;
    private Map<String, Object> parameters;
    private String messageToUser;
    private String thinking;

    public BaseResponse() {}

    public String getAgent() { return agent; }
    public void setAgent(String agent) { this.agent = agent; }

    public String getIntent() { return intent; }
    public void setIntent(String intent) { this.intent = intent; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Map<String, Object> getParameters() { return parameters; }
    public void setParameters(Map<String, Object> parameters) { this.parameters = parameters; }

    public String getMessageToUser() { return messageToUser; }
    public void setMessageToUser(String messageToUser) { this.messageToUser = messageToUser; }

    public String getThinking() { return thinking; }
    public void setThinking(String thinking) { this.thinking = thinking; }
}
