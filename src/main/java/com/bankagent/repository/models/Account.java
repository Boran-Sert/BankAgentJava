package com.bankagent.repository.models;

public class Account {
    private String id;
    private String name;
    private double balance;
    private Double monthlyInterestRate;
    private String currency;

    public Account() {}

    public Account(String id, String name, double balance, Double monthlyInterestRate, String currency) {
        this.id = id;
        this.name = name;
        this.balance = balance;
        this.monthlyInterestRate = monthlyInterestRate;
        this.currency = currency;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public double getBalance() { return balance; }
    public void setBalance(double balance) { this.balance = balance; }
    
    public Double getMonthlyInterestRate() { return monthlyInterestRate; }
    public void setMonthlyInterestRate(Double monthlyInterestRate) { this.monthlyInterestRate = monthlyInterestRate; }
    
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }
}
