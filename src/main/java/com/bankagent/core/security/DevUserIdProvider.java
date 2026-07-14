/**
 * Geliştirme (DEV) ortamında sistemi test edebilmek için sabit bir sahte (mock) kullanıcı kimliği sağlar.
 */
package com.bankagent.core.security;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

@Component
@Profile("dev")
public class DevUserIdProvider implements IUserIdProvider {

    @Override
    public String getCurrentUserId() {
        // Return hardcoded user ID for local DEV testing
        return "test_user_1";
    }
}
