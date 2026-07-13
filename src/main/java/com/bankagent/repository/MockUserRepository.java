package com.bankagent.repository;

import com.bankagent.repository.models.Account;
import com.bankagent.repository.models.Card;
import com.bankagent.repository.models.User;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;

import java.util.*;

@Repository
@ConditionalOnProperty(name = "app.use-mock-db", havingValue = "true", matchIfMissing = true)
public class MockUserRepository implements IUserRepository {

    private final Map<String, User> users = new HashMap<>();

    public MockUserRepository() {
        // Mock data initialization
        Map<String, Account> accounts = new HashMap<>();
        accounts.put("vadesiz", new Account(null, "TL Vadesiz Hesap", 15000.0, null, "TL"));
        accounts.put("vadeli", new Account("1", "TL Vadeli Hesap", 20000.0, 35.0, "TL"));
        accounts.put("vadeli2", new Account("2", "USD Vadeli Hesap", 20000.0, 35.0, "USD"));

        List<Card> cards = Arrays.asList(
            new Card(UUID.randomUUID().toString(), "4543 **** **** 9012", 15000.0, 2500.0),
            new Card(UUID.randomUUID().toString(), "5521 **** **** 1098", 5000.0, 5000.0),
            new Card(UUID.randomUUID().toString(), "4321 **** **** 3333", 20000.0, 0.0),
            new Card(UUID.randomUUID().toString(), "5100 **** **** 6666", 10000.0, 850.50),
            new Card(UUID.randomUUID().toString(), "4999 **** **** 9999", 3000.0, 1200.75)
        );

        users.put("test_user_1", new User("test_user_1", "Test Kullanıcısı", cards, accounts));
    }

    @Override
    public User getUser(String userId) {
        return users.get(userId);
    }

    @Override
    public List<Card> getUserCards(String userId) {
        User user = getUser(userId);
        return user != null ? user.getCards() : new ArrayList<>();
    }
}
