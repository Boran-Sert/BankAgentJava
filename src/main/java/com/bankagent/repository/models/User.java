/**
 * Sisteme kayıtlı olan müşterinin profil bilgilerini (Ad, Soyad, TC No vb.) temsil eden ana veri modelidir.
 */
package com.bankagent.repository.models;

import java.util.List;
import java.util.Map;

public class User {
    private String userId;
    private String name;
    private String tcNo;
    private String birthDate;
    private String profession;
    private Double monthlyIncome;
    private List<Card> cards;
    private Map<String, Account> accounts;

    public User() {}

    public User(String userId, String name, String tcNo, String birthDate, String profession, Double monthlyIncome, List<Card> cards, Map<String, Account> accounts) {
        this.userId = userId;
        this.name = name;
        this.tcNo = tcNo;
        this.birthDate = birthDate;
        this.profession = profession;
        this.monthlyIncome = monthlyIncome;
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

    public String getTcNo() { return tcNo; }
    public void setTcNo(String tcNo) { this.tcNo = tcNo; }

    public String getBirthDate() { return birthDate; }
    public void setBirthDate(String birthDate) { this.birthDate = birthDate; }

    public String getProfession() { return profession; }
    public void setProfession(String profession) { this.profession = profession; }

    public Double getMonthlyIncome() { return monthlyIncome; }
    public void setMonthlyIncome(Double monthlyIncome) { this.monthlyIncome = monthlyIncome; }
}
