package com.attributionanalysis.web.service;

import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Service;

@Service
public class PortfolioSessionService {
    private static final String PORTFOLIO_KEY = "portfolio";

    public void save(HttpSession session, String portfolio) {
        session.setAttribute(PORTFOLIO_KEY, portfolio);
    }

    public String get(HttpSession session) {
        Object value = session.getAttribute(PORTFOLIO_KEY);
        return value instanceof String s ? s : null;
    }
}
