package com.attributionanalysis.web.service;

import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@Service
public class UniverseService {

    public record UniverseEntry(String ticker, String name, String nameUpper) {}

    private volatile List<UniverseEntry> cache;

    public List<String[]> loadTickers() {
        return loadAll().stream()
                .map(e -> new String[]{e.ticker, e.name})
                .toList();
    }

    public List<UniverseEntry> loadAll() {
        if (cache != null) return cache;

        Path root = findRepoRoot();
        if (root == null) return List.of();

        List<UniverseEntry> result = new ArrayList<>();
        Path csv = root.resolve("data").resolve("reference").resolve("fmp_universe.csv");
        if (Files.exists(csv)) {
            loadCsvInto(csv, result);
        }
        cache = result;
        return result;
    }

    private void loadCsvInto(Path csv, List<UniverseEntry> result) {
        try (BufferedReader reader = Files.newBufferedReader(csv, StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            if (header == null) return;
            String[] cols = parseCsvLine(header);
            int tickerIdx = -1, nameIdx = -1, activeIdx = -1;
            for (int i = 0; i < cols.length; i++) {
                switch (cols[i].trim()) {
                    case "ticker" -> tickerIdx = i;
                    case "company_name" -> nameIdx = i;
                    case "is_active" -> activeIdx = i;
                }
            }
            if (tickerIdx < 0) return;
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = parseCsvLine(line);
                if (parts.length <= tickerIdx) continue;
                String ticker = parts[tickerIdx].trim();
                if (ticker.isEmpty()) continue;
                if (!Character.isLetter(ticker.charAt(0))) continue;
                if (ticker.length() > 5) continue;
                if (activeIdx >= 0 && parts.length > activeIdx
                        && !"True".equalsIgnoreCase(parts[activeIdx].trim())) {
                    continue;
                }
                String name = (nameIdx >= 0 && parts.length > nameIdx) ? parts[nameIdx].trim() : "";
                if (isEtfOrFund(name.toLowerCase(Locale.ROOT))) continue;
                result.add(new UniverseEntry(ticker, name, name.toUpperCase(Locale.ROOT)));
            }
        } catch (IOException e) {
            // Skip silently
        }
    }

    private static String[] parseCsvLine(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean inQuotes = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                if (inQuotes && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    current.append('"');
                    i++;
                } else {
                    inQuotes = !inQuotes;
                }
            } else if (c == ',' && !inQuotes) {
                fields.add(current.toString());
                current.setLength(0);
            } else {
                current.append(c);
            }
        }
        fields.add(current.toString());
        return fields.toArray(new String[0]);
    }

    private static final String[] ETF_TERMS = {
            "etf", " fund", "trust", " bull ", " bear ", "direxion", "proshares",
            "leveraged", "spdr", "ishares", "vanguard", " index ", "inverse",
            " ultra ", " short ", " 2x ", " 3x ", " daily ", "wisdomtree",
            "first trust", "graniteshares", "roundhill"
    };

    private static boolean isEtfOrFund(String nameLower) {
        for (String term : ETF_TERMS) {
            if (nameLower.contains(term)) return true;
        }
        return false;
    }

    private static Path findRepoRoot() {
        Path cwd = Path.of("").toAbsolutePath().normalize();
        Path cursor = cwd;
        for (int i = 0; i < 7; i++) {
            if (Files.exists(cursor.resolve("src").resolve("cli.py"))) {
                return cursor;
            }
            cursor = cursor.getParent();
            if (cursor == null) break;
        }
        return null;
    }
}
