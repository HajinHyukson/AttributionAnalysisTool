package com.attributionanalysis.web.api;

import com.attributionanalysis.web.service.PortfolioSessionService;
import com.attributionanalysis.web.service.UniverseService;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/portfolio")
public class PortfolioController {

    private final PortfolioSessionService sessionService;
    private final UniverseService universeService;

    public PortfolioController(PortfolioSessionService sessionService,
                               UniverseService universeService) {
        this.sessionService = sessionService;
        this.universeService = universeService;
    }

    @GetMapping("/universe")
    public ResponseEntity<List<String[]>> getUniverse() {
        return ResponseEntity.ok(universeService.loadTickers());
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
