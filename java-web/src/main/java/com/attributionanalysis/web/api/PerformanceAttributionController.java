package com.attributionanalysis.web.api;

import com.attributionanalysis.web.api.dto.AnalysisRequest;
import com.attributionanalysis.web.service.AnalyticsEngineService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/performance")
public class PerformanceAttributionController {

    private final AnalyticsEngineService engine;

    public PerformanceAttributionController(AnalyticsEngineService engine) {
        this.engine = engine;
    }

    @PostMapping(value = "/attribution", produces = MediaType.APPLICATION_JSON_VALUE)
    public String attribution(@RequestBody AnalysisRequest request) {
        return engine.runPerformanceAttribution(
            request.portfolio(),
            request.yearsOrDefault(),
            request.benchmarkOrDefault(),
            request.cacheOrDefault()
        );
    }
}
