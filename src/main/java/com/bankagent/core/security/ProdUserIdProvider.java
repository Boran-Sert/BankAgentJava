/**
 * Canlı (PROD) ortamda Spring Security veya JWT üzerinden gerçek kullanıcının kimliğini (ID) çeker.
 */
package com.bankagent.core.security;

import com.bankagent.core.exceptions.AiAgentException;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

@Component
@Profile("!dev") // Active in prod or any environment other than dev
public class ProdUserIdProvider implements IUserIdProvider {

    @Override
    public String getCurrentUserId() {
        // TODO: In the middleware, replace this with actual Spring Security Context, e.g.:
        // return SecurityContextHolder.getContext().getAuthentication().getName();
        
        throw new AiAgentException("Security Context extraction is not implemented in standalone agent demo for PROD.", "SECURITY_CONTEXT_MISSING");
    }
}
