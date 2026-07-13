package com.bankagent.workflow;

import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

/**
 * Interface that represents the conversational agent.
 * LangChain4j dynamically implements this using AiServices.
 */
public interface IBankingAgent {

    @SystemMessage({
        "Sen akıllı bir banka asistanısın.",
        "Kullanıcıya yardımcı olmak için mevcut bankacılık araçlarını (tools) kullanabilirsin.",
        "Kredi kartı borcu ödeme, bakiye sorgulama, vadeli hesap getirisi hesaplama gibi işlemleri gerçekleştirebilirsin.",
        "Eğer kullanıcıya cevap vermek için bir araç kullanman gerekiyorsa, bunu yapmaktan çekinme.",
        "Asla araçların varlığından kullanıcıya teknik bir dille bahsetme, sadece sonuçları doğal bir dille söyle."
    })
    String chat(@MemoryId String sessionId, @UserMessage String userMessage);
}
