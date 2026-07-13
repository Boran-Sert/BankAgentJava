package com.bankagent;

import com.bankagent.core.contracts.BaseResponse;
import com.bankagent.workflow.AgentWorkflowService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

import java.util.Scanner;

@Component
public class TerminalChatRunner implements CommandLineRunner {

    private final AgentWorkflowService agentWorkflowService;

    public TerminalChatRunner(AgentWorkflowService agentWorkflowService) {
        this.agentWorkflowService = agentWorkflowService;
    }

    @Override
    public void run(String... args) {
        System.out.println("======================================================");
        System.out.println("🏦 Java Banking Agent Terminaline Hoş Geldiniz! 🏦");
        System.out.println("======================================================");
        System.out.println("Ollama (GPT-OSS Mock) ile bağlantı kuruldu.");
        System.out.println("Çıkmak için 'exit' veya 'cikis' yazabilirsiniz.\n");

        Scanner scanner = new Scanner(System.in);
        String sessionId = "dev-session-1"; // Sabit session ID (Hafızayı tutmak için)

        while (true) {
            System.out.print("\nSen: ");
            String userInput = scanner.nextLine();

            if ("exit".equalsIgnoreCase(userInput) || "cikis".equalsIgnoreCase(userInput)) {
                System.out.println("Görüşmek üzere!");
                System.exit(0);
                break;
            }

            try {
                // Curl yerine direkt servisi çağırıyoruz.
                BaseResponse response = agentWorkflowService.processUserMessage(sessionId, userInput);
                System.out.println("\n🤖 Agent: " + response.getMessageToUser());
            } catch (Exception e) {
                System.out.println("\n❌ Sistem Hatası/Güvenlik Uyarısı: " + e.getMessage());
            }
        }
    }
}
