package com.bankagent.repository.models;

import java.util.List;
import java.util.Map;

public class User {
    private String userId;
    private String name;
    private List<Card> cards;
    private Map<String, Account> accounts;

    public User() {}

    public User(String userId, String name, List<Card> cards, Map<String, Account> accounts) {
        this.userId = userId;
        this.name = name;
        this.cards = cards;
        this.accounts = accounts;
    }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public List<Card> getCards() { return cards; }
    public void setCards(List<Card> cards) { this.cards = cards; }
    
    public Map<String, Account> getAccounts() { return accounts; }
    public void setAccounts(Map<String, Account> accounts) { this.accounts = accounts; }
}
