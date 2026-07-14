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

    @Tool("Kullanıcının hesap bakiyesini ve kredi kartı borcunu döner. 'Hesabımda ne kadar para var?' gibi sorularda kullanılır.")
    public List<Map<String, Object>> getBalance() {
        String userId = userIdProvider.getCurrentUserId();
        List<Card> cards = Optional.ofNullable(userRepository.getUserCards(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı kartları bulunamadı."));
        
        List<Map<String, Object>> result = cards.stream().map(card -> {
            Map<String, Object> cardData = new HashMap<>();
            cardData.put("card_number", card.getCardNumber());
            cardData.put("balance", card.getBalance());
            cardData.put("debt", card.getDebt());
            return cardData;
        }).collect(Collectors.toList());
        
        log.debug("getBalance executed for user: {}", userId);
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
        
        String userId = userIdProvider.getCurrentUserId();
        User user = Optional.ofNullable(userRepository.getUser(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı bilgisi bulunamadı."));

        Map<String, Account> accounts = Optional.ofNullable(user.getAccounts())
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı hesabı bulunamadı."));

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

        log.debug("calcMonthlyIncomeSavings executed for user: {}", userId);
        return results;
    }

    @Tool("Kullanıcının sahip olduğu hesapların sadece isimlerini ve ID'lerini güvenli şekilde döner. Hesap belirsizliği durumunda kullanılır.")
    public List<Map<String, Object>> getUserAccountOptions() {
        String userId = userIdProvider.getCurrentUserId();
        User user = Optional.ofNullable(userRepository.getUser(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı bilgisi bulunamadı."));

        Map<String, Account> accounts = Optional.ofNullable(user.getAccounts())
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı hesabı bulunamadı."));

        List<Map<String, Object>> safeAccounts = accounts.entrySet().stream().map(entry -> {
            Account acc = entry.getValue();
            Map<String, Object> safeAcc = new HashMap<>();
            safeAcc.put("id", acc.getId());
            safeAcc.put("name", acc.getName());
            safeAcc.put("currency", acc.getCurrency());
            safeAcc.put("type", entry.getKey().startsWith("vadeli") ? "Vadeli Hesap" : "Vadesiz Hesap");
            return safeAcc;
        }).collect(Collectors.toList());

        log.debug("getUserAccountOptions executed for user: {}", userId);
        return safeAccounts;
    }

    @Tool("Kullanıcının kredi kartlarının maskelenmiş (sadece son 4 hanesi ve kart ID'si) listesini döner.")
    public List<Map<String, Object>> getCreditCardOptions() {
        String userId = userIdProvider.getCurrentUserId();
        List<Card> cards = Optional.ofNullable(userRepository.getUserCards(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı kartları bulunamadı."));

        List<Map<String, Object>> safeCards = cards.stream().map(card -> {
            Map<String, Object> safeCard = new HashMap<>();
            String cn = card.getCardNumber();
            String last4 = (cn != null && cn.length() >= 4) ? cn.substring(cn.length() - 4) : cn;
            safeCard.put("id", cn);
            safeCard.put("masked_number", "**** **** **** " + last4);
            safeCard.put("name", "Kredi Kartı (" + last4 + ")");
            return safeCard;
        }).collect(Collectors.toList());

        log.debug("getCreditCardOptions executed for user: {}", userId);
        return safeCards;
    }

    @Tool("Kullanıcının kredi başvurusunu alır. Sadece talep edilen kredi tutarına ihtiyaç vardır. Çıktı olarak mutlaka başvuruda kullanılan tüm bilgileri içeren (TC, Ad, Doğum Tarihi, Meslek, Gelir, Tutar vb.) bir tablo oluştur.")
    public String applyForLoan(
            @P("Talep Edilen Kredi Tutarı") Double requestedAmount) {
        Map<String, Object> profile = getUserProfile();

        String filledTc = (String) profile.get("tc_no");
        String filledName = (String) profile.get("name");
        String filledBirth = (String) profile.get("birth_date");
        String filledProfession = (String) profile.get("profession");
        Double filledIncome = profile.get("monthly_income") instanceof Number ?
                ((Number)profile.get("monthly_income")).doubleValue() : null;
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
    @Tool("Kullanıcının kişisel bilgilerini getirir.")public Map<String, Object> getUserProfile() {
        String userId = userIdProvider.getCurrentUserId();
        User user = Optional.ofNullable(userRepository.getUser(userId))
                .orElseThrow(() -> new AiSkillExecutionException("Kullanıcı bilgisi bulunamadı."));

        Map<String, Object> profile = new HashMap<>();
        profile.put("name", user.getName());
        profile.put("tc_no", user.getTcNo());
        profile.put("birth_date", user.getBirthDate());
        profile.put("profession", user.getProfession());
        profile.put("monthly_income", user.getMonthlyIncome());

        log.debug("getUserProfile executed for user: {}", userId);
        return profile;
    }
}
