/**
 * Sisteme giriş yapmış olan kullanıcının kimlik bilgisini (ID) sağlayan ortak bir sözleşmedir (Interface).
 */
package com.bankagent.core.security;

public interface IUserIdProvider {
    String getCurrentUserId();
}
