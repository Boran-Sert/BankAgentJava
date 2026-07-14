package com.bankagent.skills;

import com.bankagent.core.exceptions.AiSkillExecutionException;
import com.bankagent.core.security.IUserIdProvider;
import com.bankagent.repository.IUserRepository;
import com.bankagent.repository.models.Account;
import com.bankagent.repository.models.Card;
import com.bankagent.repository.models.User;
import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.P;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.stream.Collectors;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;

@Component
public class BankingSkills {

    private static final Logger log = LoggerFactory.getLogger(BankingSkills.class);
    private final IUserRepository userRepository;
    private final IUserIdProvider userIdProvider;

    public BankingSkills(IUserRepository userRepository, IUserIdProvider userIdProvider) {
        this.userRepository = userRepository;
        this.userIdProvider = userIdProvider;
    }

    // --- TEMEL YARDIMCI METOTLAR (BASE HELPERS) ---
    private User getCurrentUser() {
        String userId = userIdProvider.getCurrentUserId();
        return Optional.ofNullable(userRepository.getUser(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı bilgisi bulunamadı."));
    }

    private List<Card> getAllCards() {
        String userId = userIdProvider.getCurrentUserId();
        return Optional.ofNullable(userRepository.getUserCards(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı kartları bulunamadı."));
    }

    private Map<String, Account> getAllAccounts() {
        return Optional.ofNullable(getCurrentUser().getAccounts())
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı hesabı bulunamadı."));
    }

    private List<Account> getForeignCurrencyAccounts() {
        return getAllAccounts().values().stream()
                .filter(acc -> !"TRY".equalsIgnoreCase(acc.getCurrency()))
                .collect(Collectors.toList());
    }
    // ----------------------------------------------

    @Tool("Kullanıcının hesap bakiyesini ve kredi kartı borcunu döner. 'Hesabımda ne kadar para var?' gibi sorularda kullanılır.")
    public List<Map<String, Object>> getBalance() {
        List<Card> cards = getAllCards();
        
        List<Map<String, Object>> result = cards.stream().map(card -> {
            Map<String, Object> cardData = new HashMap<>();
            cardData.put("card_number", card.getCardNumber());
            cardData.put("balance", card.getBalance());
            cardData.put("debt", card.getDebt());
            return cardData;
        }).collect(Collectors.toList());
        
        log.debug("getBalance executed for user: {}", userIdProvider.getCurrentUserId());
        return result;
    }

// ------------------------------------ GERÇEK BİR TOOL OLARAK KULLANILMAYACAK SADECE TEST AMAÇLI --------------------------------------
    @Tool("Kredi kartı borcunu öder veya karta para yatırır.")
    public Map<String, Object> makePayment(
            @P("Kredi Kartı Numarası (Son 4 hanesi veya ilk 4 hanesi veya tam numarası olabilir)") String cardId,
            @P("Ödenecek Tutar") double amount) {
        
        if (cardId == null || cardId.isEmpty() || amount <= 0) {
            throw new AiSkillExecutionException("Ödeme işlemi için eksik veya geçersiz parametreler.");
        }

        Map<String, Object> result = new HashMap<>();
        result.put("status", "success");
        result.put("action", "MAKE_PAYMENT");
        result.put("card_id", cardId);
        result.put("paid_amount", amount);
        result.put("remaining_debt", 0.0); // Mocked
        
        log.debug("makePayment executed for card {}", cardId);
        return result;
    }
    // ------------------------------------ GERÇEK BİR TOOL OLARAK KULLANILMAYACAK SADECE TEST AMAÇLI --------------------------------------

    @Tool("Belirli vadeli hesaplarındaki aylık faiz getirisini hesaplar ve döner.")
    public List<Map<String, Object>> calcMonthlyIncomeSavings(
            @P("Aylık faizi hesaplanacak vadeli hesabın benzersiz ID'lerinin listesi (örn: ['1', '2'])") List<String> accountIds) {
        
        Map<String, Account> accounts = getAllAccounts();

        List<Map<String, Object>> results = accountIds.stream().map(accId -> {
            Optional<Account> targetAccount = accounts.entrySet().stream()
                    .filter(entry -> entry.getKey().startsWith("vadeli") && accId.equals(entry.getValue().getId()))
                    .map(Map.Entry::getValue)
                    .findFirst();

            Map<String, Object> res = new HashMap<>();
            if (targetAccount.isPresent()) {
                Account acc = targetAccount.get();
                double balance = acc.getBalance();
                double monthlyRate = acc.getMonthlyInterestRate() != null ? acc.getMonthlyInterestRate() : 0.0;
                double monthlyIncome = (balance * (monthlyRate / 100)) / 12;
                
                res.put("id", acc.getId());
                res.put("name", acc.getName());
                res.put("balance", balance);
                res.put("monthly_interest_income", monthlyIncome);
                res.put("currency", acc.getCurrency());
            } else {
                throw new AiSkillExecutionException("Belirtilen ID'ye sahip bir vadeli hesap bulunamadı: " + accId);
            }
            return res;
        }).collect(Collectors.toList());

        log.debug("calcMonthlyIncomeSavings executed for user: {}", userIdProvider.getCurrentUserId());
        return results;
    }

    @Tool("Kullanıcının sahip olduğu hesapların sadece isimlerini ve ID'lerini güvenli şekilde döner. Hesap belirsizliği durumunda kullanılır.")
    public List<Map<String, Object>> getUserAccountOptions() {
        Map<String, Account> accounts = getAllAccounts();

        List<Map<String, Object>> safeAccounts = accounts.entrySet().stream().map(entry -> {
            Account acc = entry.getValue();
            Map<String, Object> safeAcc = new HashMap<>();
            safeAcc.put("id", acc.getId());
            safeAcc.put("name", acc.getName());
            safeAcc.put("currency", acc.getCurrency());
            safeAcc.put("type", entry.getKey().startsWith("vadeli") ? "Vadeli Hesap" : "Vadesiz Hesap");
            return safeAcc;
        }).collect(Collectors.toList());

        log.debug("getUserAccountOptions executed for user: {}", userIdProvider.getCurrentUserId());
        return safeAccounts;
    }

    @Tool("Kullanıcının kredi kartlarının maskelenmiş (sadece son 4 hanesi ve kart ID'si) listesini döner.")
    public List<Map<String, Object>> getCreditCardOptions() {
        List<Card> cards = getAllCards();

        List<Map<String, Object>> safeCards = cards.stream().map(card -> {
            Map<String, Object> safeCard = new HashMap<>();
            String cn = card.getCardNumber();
            String last4 = (cn != null && cn.length() >= 4) ? cn.substring(cn.length() - 4) : cn;
            safeCard.put("id", cn);
            safeCard.put("masked_number", "**** **** **** " + last4);
            safeCard.put("name", "Kredi Kartı (" + last4 + ")");
            return safeCard;
        }).collect(Collectors.toList());

        log.debug("getCreditCardOptions executed for user: {}", userIdProvider.getCurrentUserId());
        return safeCards;
    }

    @Tool("Kullanıcının kredi başvurusunu alır. Sadece talep edilen kredi tutarına ihtiyaç vardır. Çıktı olarak mutlaka başvuruda kullanılan tüm bilgileri içeren (TC, Ad, Doğum Tarihi, Meslek, Gelir, Tutar vb.) bir tablo oluştur.")
    public String applyForLoan(
            @P("Talep Edilen Kredi Tutarı") Double requestedAmount) {
        
        User user = getCurrentUser();

        String filledTc = user.getTcNo();
        String filledName = user.getName();
        String filledBirth = user.getBirthDate();
        String filledProfession = user.getProfession();
        Double filledIncome = user.getMonthlyIncome();
        
        if (filledTc == null || filledName == null || filledBirth == null ||
                filledIncome == null || requestedAmount == null) {
            throw new AiSkillExecutionException("Kredi başvurusu için kullanıcı profilindeki bilgiler eksik.");
        }
        
        Map<String,Object> payload = new HashMap<>();
        payload.put("tcNo", filledTc);
        payload.put("fullName", filledName);
        payload.put("birthDate", filledBirth);
        payload.put("profession", filledProfession);
        payload.put("monthlyIncome", filledIncome);
        payload.put("requestedAmount", requestedAmount);
        payload.put("submittedByUserId", userIdProvider.getCurrentUserId());
        payload.put("timestamp", new Date().toString());

        // Return JSON string so LLM receives filled parameters (tool result), no UI form
        try {
            return new ObjectMapper().writeValueAsString(payload);
        } catch (JsonProcessingException e) {
            throw new AiSkillExecutionException("Başvuru JSON'a dönüştürülürken hata: " + e.getMessage(), e);
        }
    }

    @Tool("Kullanıcının kişisel bilgilerini getirir.")
    public Map<String, Object> getUserProfile() {
        User user = getCurrentUser();

        Map<String, Object> profile = new HashMap<>();
        profile.put("name", user.getName());
        profile.put("tc_no", user.getTcNo());
        profile.put("birth_date", user.getBirthDate());
        profile.put("profession", user.getProfession());
        profile.put("monthly_income", user.getMonthlyIncome());

        log.debug("getUserProfile executed for user: {}", userIdProvider.getCurrentUserId());
        return profile;
    }

    @Tool("Kullanıcının yatırım fonlarının getirisini hesaplar. Kullanıcı 'tüm fonlarım' derse fon kodunu boş liste olarak gönderebilirsiniz.")
    public Map<String, Object> calculateInvestmentReturns(
            @P("Yatırım fonlarının kodları. Kullanıcı tüm fonları kastettiyse boş bırakılabilir (örn: ['AFA'])") List<String> fundCodes,
            @P("Kaç günlük getiri hesaplanacağı") int days) {
        
        User user = getCurrentUser();
        Map<String, Account> allAccounts = getAllAccounts();
        Map<String, Object> investmentReturns = new HashMap<>();
        
        if (days <= 0) {
            throw new AiSkillExecutionException("Yatırım getirisi hesaplamak için geçerli bir gün sayısı gereklidir.");
        }
        
        // Kullanıcının sahip olduğu yatırım fonu hesaplarını filtrele (isimleri 'Fonu' kelimesi içeriyorsa)
        List<Account> userFundAccounts = allAccounts.values().stream()
                .filter(acc -> acc.getName() != null && acc.getName().contains("Fonu"))
                .toList();
        
        if (fundCodes == null || fundCodes.isEmpty()) {
            // Fon kodu belirtilmemişse kullanıcının sahip olduğu tüm fonları dahil et
            fundCodes = userFundAccounts.stream()
                    .map(acc -> acc.getName().split(" ")[0]) // Örn: "AFA - Ak Portföy..." -> "AFA"
                    .collect(Collectors.toList());
        }
        
        List<Map<String, Object>> fundResults = new ArrayList<>();
        double totalProfit = 0.0;
        double actualTotalInvestment = 0.0;
        
        // Mock getiri hesaplaması (gerçek hayatta banka veya borsa API'sinden çekilir)
        for (String fundCode : fundCodes) {
            // Kullanıcının hesapları içinde bu fonu ara
            Optional<Account> fundAccountOpt = userFundAccounts.stream()
                    .filter(acc -> acc.getName().startsWith(fundCode))
                    .findFirst();
            
            if (fundAccountOpt.isEmpty()) {
                continue; // Kullanıcının böyle bir fonu yoksa atla
            }
            
            Account fundAccount = fundAccountOpt.get();
            double investedAmount = fundAccount.getBalance();
            actualTotalInvestment += investedAmount;
            
            Map<String, Object> fundData = new HashMap<>();
            fundData.put("fund_code", fundCode);
            
            // Random mock interest rate (örneğin günlük %0.05 - %0.3 arası rastgele bir getiri)
            double dailyRate = 0.0005 + (Math.random() * 0.0025); 
            double totalRate = dailyRate * days;
            double profit = investedAmount * totalRate;
            
            fundData.put("invested_amount", Math.round(investedAmount * 100.0) / 100.0);
            fundData.put("profit", Math.round(profit * 100.0) / 100.0);
            fundData.put("total_amount", Math.round((investedAmount + profit) * 100.0) / 100.0);
            fundData.put("rate_of_return_percentage", Math.round(totalRate * 10000.0) / 100.0);
            
            totalProfit += profit;
            fundResults.add(fundData);
        }
        
        if (fundResults.isEmpty()) {
            throw new AiSkillExecutionException("Belirtilen fon kodlarına ait yatırım hesabı bulunamadı.");
        }
        
        investmentReturns.put("user_name", user.getName());
        investmentReturns.put("days", days);
        investmentReturns.put("funds", fundResults);
        investmentReturns.put("total_invested", Math.round(actualTotalInvestment * 100.0) / 100.0);
        investmentReturns.put("total_profit", Math.round(totalProfit * 100.0) / 100.0);
        investmentReturns.put("final_total", Math.round((actualTotalInvestment + totalProfit) * 100.0) / 100.0);
        
        log.debug("calculateInvestmentReturns executed for user: {}", userIdProvider.getCurrentUserId());
        return investmentReturns;
    }
}
