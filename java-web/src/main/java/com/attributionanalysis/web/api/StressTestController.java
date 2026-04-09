package com.attributionanalysis.web.api;

import com.attributionanalysis.web.api.dto.AnalysisRequest;
import com.attributionanalysis.web.service.AnalyticsEngineService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/stress")
public class StressTestController {

    private final AnalyticsEngineService engine;

    public StressTestController(AnalyticsEngineService engine) {
        this.engine = engine;
    }

    @PostMapping(value = "/test", produces = MediaType.APPLICATION_JSON_VALUE)
    public String test(@RequestBody AnalysisRequest request) {
        return engine.runStressTest(
            request.portfolio(),
            request.yearsOrDefault(),
            request.scenariosOrDefault(),
            request.cacheOrDefault()
        );
    }
}
