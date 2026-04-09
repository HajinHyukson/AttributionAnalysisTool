package com.attributionanalysis.web.api;

import com.attributionanalysis.web.service.PortfolioSessionService;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/portfolio")
public class PortfolioController {

    private final PortfolioSessionService sessionService;

    public PortfolioController(PortfolioSessionService sessionService) {
        this.sessionService = sessionService;
    }

    @PostMapping("/save")
    public ResponseEntity<Map<String, String>> save(
            @RequestBody Map<String, String> body,
            HttpSession session) {
        String portfolio = body.get("portfolio");
        if (portfolio == null || portfolio.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "portfolio is required"));
        }
        sessionService.save(session, portfolio);
        return ResponseEntity.ok(Map.of("status", "saved"));
    }

    @GetMapping("/current")
    public ResponseEntity<Map<String, String>> current(HttpSession session) {
        String portfolio = sessionService.get(session);
        if (portfolio == null) {
            return ResponseEntity.ok(Map.of("portfolio", ""));
        }
        return ResponseEntity.ok(Map.of("portfolio", portfolio));
    }
}
