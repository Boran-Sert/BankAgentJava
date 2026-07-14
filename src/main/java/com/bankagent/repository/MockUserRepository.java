package com.bankagent.repository;

import com.bankagent.repository.models.Account;
import com.bankagent.repository.models.Card;
import com.bankagent.repository.models.User;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;

import java.util.*;
// BİR DATABASE MOCKLAMAK İÇİN YAPILMIŞTIR
@Repository
@ConditionalOnProperty(name = "app.use-mock-db", havingValue = "true", matchIfMissing = true)
public class MockUserRepository implements IUserRepository {

    private final Map<String, User> users = new HashMap<>();

    public MockUserRepository() {
        // Mock data initialization
        Map<String, Account> accounts = new HashMap<>();
        // Vadesiz (Checking) Accounts
        accounts.put("vadesiz_tl", new Account(null, "Maaş Hesabı (TL)", 18500.75, null, "TRY"));
        accounts.put("vadesiz_tl", new Account(null, "Cari Hesap (TL)", 20000.75, null, "TRY"));
        accounts.put("vadesiz_usd", new Account(null, "Yurtdışı Harcama (USD)", 1250.00, null, "USD"));
        accounts.put("vadesiz_eur", new Account(null, "Avrupa Seyahat (EUR)", 450.50, null, "EUR"));

        // Vadeli (Savings / Deposit) Accounts
        accounts.put("vadeli_tl_32", new Account("1", "32 Günlük Vadeli (TL)", 150000.00, 42.5, "TRY"));
        accounts.put("vadeli_tl_90", new Account("2", "90 Günlük Kur Korumalı (TL)", 500000.00, 35.0, "TRY"));
        accounts.put("vadeli_usd_180", new Account("3", "6 Aylık Döviz Tevdiat (USD)", 25000.00, 3.5, "USD"));

        // Yatırım / Altın
        accounts.put("yatirim_altin", new Account("4", "Vadesiz Altın Hesabı", 125.4, null, "XAU")); // Gram altın
        accounts.put("yatirim_fon", new Account("5", "A Tipi Hisse Senedi Fonu", 85000.00, null, "TRY"));

        List<Card> cards = Arrays.asList(
            // Kredi Kartları (Credit Cards)
            new Card(UUID.randomUUID().toString(), "Platinum Visa - 4543 **** **** 9012", 150000.0, 12500.45),
            new Card(UUID.randomUUID().toString(), "Miles&Smiles Mastercard - 5521 **** **** 1098", 200000.0, 45000.00),
            new Card(UUID.randomUUID().toString(), "Öğrenci Genç Kart - 4321 **** **** 3333", 10000.0, 0.0),
            new Card(UUID.randomUUID().toString(), "Sanal Kart (Online Alışveriş) - 5100 **** **** 6666", 5000.0, 850.50),
            
            // Banka Kartları (Debit Cards) - Genelde limit yerine bakiye olur ama modelde limit var.
            new Card(UUID.randomUUID().toString(), "Maaş Banka Kartı (Troy) - 4999 **** **** 9999", 18500.75, 0.0)
        );

        users.put("test_user_1", new User("test_user_1", "Boran Sert", "12345678901", "1990-05-15", "Yazılım Mühendisi", 85000.0, cards, accounts));
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
