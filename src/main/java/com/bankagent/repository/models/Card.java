package com.bankagent.repository.models;

public class Card {
    private String id;
    private String cardNumber;
    private double balance;
    private double debt;

    public Card() {}

    public Card(String id, String cardNumber, double balance, double debt) {
        this.id = id;
        this.cardNumber = cardNumber;
        this.balance = balance;
        this.debt = debt;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getCardNumber() { return cardNumber; }
    public void setCardNumber(String cardNumber) { this.cardNumber = cardNumber; }
    
    public double getBalance() { return balance; }
    public void setBalance(double balance) { this.balance = balance; }
    
    public double getDebt() { return debt; }
    public void setDebt(double debt) { this.debt = debt; }
}
