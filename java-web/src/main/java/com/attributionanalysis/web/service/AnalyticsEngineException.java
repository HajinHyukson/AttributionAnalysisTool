package com.attributionanalysis.web.service;

public class AnalyticsEngineException extends RuntimeException {
    private final String details;

    public AnalyticsEngineException(String message, String details) {
        super(message);
        this.details = details;
    }

    public String getDetails() {
        return details;
    }
}
