package com.attributionanalysis.web.api.dto;

public record AnalysisRequest(
    String portfolio,
    Integer years,
    String benchmark,
    Boolean cache,
    Integer nFactors,
    Integer window,
    String scenarios
) {
    public int yearsOrDefault() { return years != null ? years : 3; }
    public String benchmarkOrDefault() { return benchmark != null ? benchmark : "SPY"; }
    public boolean cacheOrDefault() { return cache == null || cache; }
    public int nFactorsOrDefault() { return nFactors != null ? nFactors : 3; }
    public int windowOrDefault() { return window != null ? window : 60; }
    public String scenariosOrDefault() {
        return scenarios != null ? scenarios : "GFC_2008,COVID_2020,RATE_HIKES_2022";
    }
}
