package com.attributionanalysis.web.api;

import com.attributionanalysis.web.service.AnalyticsEngineService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/stock")
public class StockController {

    private final AnalyticsEngineService engine;
    private final ObjectMapper mapper = new ObjectMapper();

    public StockController(AnalyticsEngineService engine) {
        this.engine = engine;
    }

    @GetMapping("/search")
    public ResponseEntity<?> search(
            @RequestParam String q,
            @RequestParam(defaultValue = "20") int limit) {
        String json = engine.runSearchStocks(q, limit, true);
        try {
            List<Map<String, String>> results = mapper.readValue(
                    json, new TypeReference<>() {});
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            return ResponseEntity.ok(json);
        }
    }

    @GetMapping("/quote")
    public ResponseEntity<?> quote(@RequestParam String tickers) {
        String json = engine.runQuote(tickers, false);
        try {
            Map<String, Double> prices = mapper.readValue(
                    json, new TypeReference<>() {});
            return ResponseEntity.ok(prices);
        } catch (Exception e) {
            return ResponseEntity.ok(json);
        }
    }
}
