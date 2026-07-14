/**
 * Proje genelindeki tüm istisnaları (Exception) tek bir noktada yakalayıp güvenli API yanıtlarına dönüştürür.
 */
package com.bankagent.core.exceptions;

import com.bankagent.core.contracts.BaseResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(AiAgentException.class)
    public ResponseEntity<BaseResponse> handleAiAgentException(AiAgentException ex) {
        log.error("AI Agent Exception [{}]: {}", ex.getErrorCode(), ex.getMessage(), ex);
        
        BaseResponse response = new BaseResponse();
        response.setAgent("JavaBankingAgent");
        response.setStatus("ERROR");
        response.setMessageToUser("Sistemde geçici bir hata oluştu. Lütfen daha sonra tekrar deneyiniz.");
        
        Map<String, Object> params = new HashMap<>();
        params.put("errorCode", ex.getErrorCode());
        response.setParameters(params);
        
        return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @ExceptionHandler(AiGuardrailException.class)
    public ResponseEntity<BaseResponse> handleAiGuardrailException(AiGuardrailException ex) {
        log.warn("AI Guardrail Exception: {}", ex.getMessage());
        
        BaseResponse response = new BaseResponse();
        response.setAgent("JavaBankingAgent");
        response.setStatus("BLOCKED");
        response.setMessageToUser("İşleminiz güvenlik kurallarına takıldığı için engellenmiştir.");
        
        Map<String, Object> params = new HashMap<>();
        params.put("errorCode", ex.getErrorCode());
        response.setParameters(params);
        
        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<BaseResponse> handleValidationExceptions(MethodArgumentNotValidException ex) {
        log.warn("Validation Error: {}", ex.getMessage());
        
        BaseResponse response = new BaseResponse();
        response.setAgent("JavaBankingAgent");
        response.setStatus("INVALID_REQUEST");
        response.setMessageToUser("Girdiğiniz bilgiler geçersiz. Lütfen kontrol edip tekrar deneyin.");
        
        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<BaseResponse> handleGlobalException(Exception ex) {
        log.error("Unexpected Exception: ", ex);
        
        BaseResponse response = new BaseResponse();
        response.setAgent("JavaBankingAgent");
        response.setStatus("SYSTEM_ERROR");
        response.setMessageToUser("Beklenmeyen bir sistem hatası oluştu.");
        
        return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
