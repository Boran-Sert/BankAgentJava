/**
 * Kullanıcı ve hesap verilerine ulaşmak için kullanılan veri tabanı erişim katmanının (Repository) arayüzüdür.
 */
package com.bankagent.repository;

import com.bankagent.repository.models.Card;
import com.bankagent.repository.models.User;
import java.util.List;

public interface IUserRepository {
    User getUser(String userId);
    List<Card> getUserCards(String userId);
}
