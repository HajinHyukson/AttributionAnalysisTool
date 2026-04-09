package com.attributionanalysis.web.api;

import com.attributionanalysis.web.service.AnalyticsEngineException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(AnalyticsEngineException.class)
    public ResponseEntity<Map<String, String>> handleEngineError(AnalyticsEngineException ex) {
        return ResponseEntity.internalServerError().body(Map.of(
            "error", ex.getMessage(),
            "details", ex.getDetails() != null ? ex.getDetails() : ""
        ));
    }
}
