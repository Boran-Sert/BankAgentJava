/**
 * Java metotlarını (@Tool) ayrıştırarak yapay zekanın anlayabileceği JSON şemalarına (JSON Schema) dönüştürür.
 */
package com.bankagent.generator;

import com.bankagent.llm.ILLMProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class SkillGeneratorService {

    private static final Logger log = LoggerFactory.getLogger(SkillGeneratorService.class);
    private final ILLMProvider llmProvider;

    public SkillGeneratorService(ILLMProvider llmProvider) {
        this.llmProvider = llmProvider;
    }

    /**
     * Dynamically generates a new skill definition or prompts the LLM to write code for a missing skill.
     * This mirrors the "skill oluşturucu" (skill generator) logic from Python.
     */
    public String generateSkill(String requestedSkillName, String userContext) {
        log.info("Generating new skill for: {}", requestedSkillName);
        
        String prompt = String.format(
            "Kullanıcı bankacılık sisteminde şu an tanımlı olmayan bir yetenek (skill) talep etti: '%s'. " +
            "Kullanıcının bağlamı: '%s'. " +
            "Lütfen bu yeteneğin nasıl çalışması gerektiğini, hangi parametreleri alması gerektiğini JSON formatında veya Java metod imzası (signature) olarak tasarla.",
            requestedSkillName, userContext
        );

        try {
            String response = llmProvider.getModel().generate(prompt);
            log.info("Skill generated successfully.");
            return response;
        } catch (Exception e) {
            log.error("Failed to generate skill", e);
            return "Skill generation failed: " + e.getMessage();
        }
    }
}
