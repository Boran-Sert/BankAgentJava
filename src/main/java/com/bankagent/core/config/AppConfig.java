/**
 * Uygulamanın genel Jackson ve Spring Bean yapılandırmalarını (konfigürasyonlarını) barındırır.
 */
package com.bankagent.core.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private boolean useMockDb;

    public boolean isUseMockDb() {
        return useMockDb;
    }

    public void setUseMockDb(boolean useMockDb) {
        this.useMockDb = useMockDb;
    }
}
