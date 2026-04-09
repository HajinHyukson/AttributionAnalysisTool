package com.attributionanalysis.web.api;

import com.attributionanalysis.web.api.dto.AnalysisRequest;
import com.attributionanalysis.web.service.AnalyticsEngineService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/correlation")
public class CorrelationRegimeController {

    private final AnalyticsEngineService engine;

    public CorrelationRegimeController(AnalyticsEngineService engine) {
        this.engine = engine;
    }

    @PostMapping(value = "/regime", produces = MediaType.APPLICATION_JSON_VALUE)
    public String regime(@RequestBody AnalysisRequest request) {
        return engine.runCorrelationRegime(
            request.portfolio(),
            request.yearsOrDefault(),
            request.windowOrDefault(),
            request.cacheOrDefault()
        );
    }
}
