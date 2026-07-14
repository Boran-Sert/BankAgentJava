/**
 * Router ajanından gelen karara göre isteği ilgili uzman ajana (Strategy) yönlendiren ana iş akışı servisidir.
 */
package com.bankagent.workflow;

import com.bankagent.core.contracts.BaseResponse;
import com.bankagent.guardrails.GuardrailsService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class AgentWorkflowService {

    private static final Logger log = LoggerFactory.getLogger(AgentWorkflowService.class);

    private final IRouterAgent routerAgent;
    private final GuardrailsService guardrailsService;
    private final Map<AgentRoute, IAgentWorkflowStrategy> strategies;
    private final WorkflowLogger workflowLogger;

    public AgentWorkflowService(IRouterAgent routerAgent, 
                                GuardrailsService guardrailsService, 
                                List<IAgentWorkflowStrategy> strategyList,
                                WorkflowLogger workflowLogger) {
        this.routerAgent = routerAgent;
        this.guardrailsService = guardrailsService;
        this.workflowLogger = workflowLogger;
        
        // NullPointerException ve DuplicateKeyException'a karşı korumalı Map dönüşümü
        this.strategies = Optional.ofNullable(strategyList)
                .orElse(List.of())
                .stream()
                .collect(Collectors.toMap(
                        IAgentWorkflowStrategy::getRoute, 
                        Function.identity(), 
                        (existing, replacement) -> {
                            log.warn("Duplicate strategy found for route {}. Keeping existing: {}", existing.getRoute(), existing.getClass().getSimpleName());
                            return existing;
                        }
                ));
    }

    public BaseResponse processUserMessage(String sessionId, String userMessage) {
        // 1. Girdi Güvenliği (Guardrails)
        guardrailsService.validateInput(userMessage);
        workflowLogger.logInput(userMessage);
        
        // 2. Router ile Niyet Analizi (Hata korumalı)
        AgentRoute route = determineRouteSafely(sessionId, userMessage);
        workflowLogger.logRouting(route);

        // 3. Strateji Seçimi (Hata korumalı)
        IAgentWorkflowStrategy strategy = getStrategySafely(route);
        
        // 4. Stratejiyi Çalıştırma
        String aiResponse = executeStrategySafely(strategy, sessionId, userMessage);
        workflowLogger.logFinalResponse();
        
        // 5. Çıktı Güvenliği (Guardrails)
        String safeResponse = sanitizeOutputSafely(aiResponse);
        
        return buildResponse(route, safeResponse);
    }

    /**
     * LLM tabanlı yönlendiricilerde yaşanabilecek "Null" dönme veya Exception fırlatma durumlarını engeller.
     */
    private AgentRoute determineRouteSafely(String sessionId, String userMessage) {
        try {
            AgentRoute route = routerAgent.route(sessionId, userMessage);
            if (route == null) {
                log.warn("Router returned null intent, defaulting to GENERAL.");
                return AgentRoute.GENERAL;
            }
            return route;
        } catch (Exception e) {
            log.error("Router failed to determine intent due to error: {}, defaulting to GENERAL.", e.getMessage());
            return AgentRoute.GENERAL;
        }
    }

    /**
     * İlgili rotaya ait strateji bulunamadığında oluşacak NullPointerException hatalarını önler.
     */
    private IAgentWorkflowStrategy getStrategySafely(AgentRoute route) {
        IAgentWorkflowStrategy strategy = strategies.get(route);
        if (strategy == null) {
            log.warn("No strategy found for route {}, attempting fallback to GENERAL.", route);
            strategy = strategies.get(AgentRoute.GENERAL);
        }
        
        // Sistemde fallback yapacak GENERAL stratejisi bile yoksa Fast-Fail uygulanır
        if (strategy == null) {
            throw new IllegalStateException("Kritik Hata: Sistemde isteği işleyecek hiçbir ajan stratejisi bulunamadı!");
        }
        
        return strategy;
    }

    /**
     * Ajanların içerisinde olası kod hatalarında uygulamanın çökmesini önler.
     */
    private String executeStrategySafely(IAgentWorkflowStrategy strategy, String sessionId, String userMessage) {
        try {
            String response = strategy.execute(sessionId, userMessage);
            return response != null ? response : "Ajan boş yanıt döndürdü.";
        } catch (Exception e) {
            log.error("Strategy execution failed for route: {}", strategy.getRoute(), e);
            return "Şu anda sistemde bir hata oluştu, işleminizi gerçekleştiremiyoruz. Lütfen daha sonra tekrar deneyiniz.";
        }
    }
    
    /**
     * Guardrails filtresi sırasında çıkabilecek hataları engeller.
     */
    private String sanitizeOutputSafely(String aiResponse) {
        try {
            return guardrailsService.sanitizeOutput(aiResponse);
        } catch (Exception e) {
            log.error("Failed to sanitize agent output", e);
            return "Sistem hatası: Yanıt güvenlik kontrolünden geçemedi.";
        }
    }

    private BaseResponse buildResponse(AgentRoute route, String safeResponse) {
        BaseResponse response = new BaseResponse();
        response.setAgent("MultiAgentSystem (" + route.name() + ")");
        response.setIntent(route.name());
        response.setStatus("COMPLETED");
        response.setMessageToUser(safeResponse);
        return response;
    }
}
