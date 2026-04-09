package com.attributionanalysis.web.service;

import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

@Service
public class AnalyticsEngineService {
    private static final Duration PROCESS_TIMEOUT = Duration.ofSeconds(300);

    public String runRiskAttribution(String portfolio, int years, int nFactors, boolean cache) {
        List<String> args = List.of(
            "-m", "src.cli", "risk-attribution",
            "--portfolio", portfolio,
            "--years", Integer.toString(years),
            "--n-factors", Integer.toString(nFactors),
            cache ? "--cache" : "--no-cache"
        );
        return runPython(args);
    }

    public String runPerformanceAttribution(String portfolio, int years, String benchmark, boolean cache) {
        List<String> args = List.of(
            "-m", "src.cli", "performance-attribution",
            "--portfolio", portfolio,
            "--years", Integer.toString(years),
            "--benchmark", benchmark,
            cache ? "--cache" : "--no-cache"
        );
        return runPython(args);
    }

    public String runStressTest(String portfolio, int years, String scenarios, boolean cache) {
        List<String> args = List.of(
            "-m", "src.cli", "stress-test",
            "--portfolio", portfolio,
            "--years", Integer.toString(years),
            "--scenarios", scenarios,
            cache ? "--cache" : "--no-cache"
        );
        return runPython(args);
    }

    public String runSearchStocks(String query, int limit, boolean cache) {
        List<String> args = List.of(
            "-m", "src.cli", "search-stocks",
            "--query", query,
            "--limit", Integer.toString(limit),
            cache ? "--cache" : "--no-cache"
        );
        return runPython(args);
    }

    public String runQuote(String tickers, boolean cache) {
        List<String> args = List.of(
            "-m", "src.cli", "quote",
            "--tickers", tickers,
            cache ? "--cache" : "--no-cache"
        );
        return runPython(args);
    }

    public String runCorrelationRegime(String portfolio, int years, int window, boolean cache) {
        List<String> args = List.of(
            "-m", "src.cli", "correlation-regime",
            "--portfolio", portfolio,
            "--years", Integer.toString(years),
            "--window", Integer.toString(window),
            cache ? "--cache" : "--no-cache"
        );
        return runPython(args);
    }

    private String runPython(List<String> args) {
        Path root = findRepoRoot();
        if (root == null) {
            throw new AnalyticsEngineException(
                "Analytics engine failed",
                "Unable to find src/cli.py from current path: " + Path.of("").toAbsolutePath()
            );
        }

        List<String> commands = pythonCommands();
        List<String> failures = new ArrayList<>();
        ProcessResult result = null;

        for (String command : commands) {
            result = runCommand(command, args, root);
            if (result.exitCode() == 0) {
                break;
            }
            String details = (result.stderr().isBlank() ? result.stdout() : result.stderr()).trim();
            String detailsLower = details.toLowerCase(Locale.ROOT);
            failures.add("[" + command + "] " + (details.isBlank() ? "no error output" : details));
            if (!detailsLower.contains("not found")
                    && !detailsLower.contains("no such file")
                    && !detailsLower.contains("cannot find")
                    && !detailsLower.contains("createprocess error=2")) {
                break;
            }
        }

        if (result == null || result.exitCode() != 0) {
            throw new AnalyticsEngineException(
                "Analytics engine failed",
                String.join("\n\n", failures)
            );
        }

        return result.stdout().trim();
    }

    private static List<String> pythonCommands() {
        List<String> candidates = new ArrayList<>();
        String fromEnv = System.getenv("PYTHON_PATH");
        if (fromEnv != null && !fromEnv.isBlank()) {
            candidates.add(fromEnv.trim());
        }
        candidates.add(".venv/Scripts/python.exe");
        candidates.add(".venv/bin/python3");
        candidates.add(".venv/bin/python");
        candidates.add("python3");
        candidates.add("python");
        candidates.add("py");
        return candidates;
    }

    private static Path findRepoRoot() {
        Path cwd = Path.of("").toAbsolutePath().normalize();
        List<Path> candidates = new ArrayList<>();
        candidates.add(cwd);
        Path cursor = cwd;
        for (int i = 0; i < 6; i++) {
            cursor = cursor.getParent();
            if (cursor == null) break;
            candidates.add(cursor);
        }
        for (Path candidate : candidates) {
            if (Files.exists(candidate.resolve("src").resolve("cli.py"))) {
                return candidate;
            }
        }
        return null;
    }

    private static ProcessResult runCommand(String command, List<String> args, Path root) {
        String resolvedCommand = command;
        if (command.contains("/") || command.contains("\\")) {
            Path commandPath = Path.of(command);
            if (!commandPath.isAbsolute()) {
                commandPath = root.resolve(commandPath);
            }
            resolvedCommand = commandPath.toString();
        }

        List<String> full = new ArrayList<>();
        full.add(resolvedCommand);
        if ("py".equals(command)) {
            full.add("-3");
        }
        full.addAll(args);

        ProcessBuilder builder = new ProcessBuilder(full);
        builder.directory(root.toFile());
        builder.environment().put("PYTHONUNBUFFERED", "1");

        try {
            Process process = builder.start();
            AtomicReference<String> stdoutRef = new AtomicReference<>("");
            AtomicReference<String> stderrRef = new AtomicReference<>("");

            Thread stdoutThread = new Thread(() -> {
                try (InputStream stream = process.getInputStream()) {
                    stdoutRef.set(slurp(stream));
                } catch (Exception ignored) {}
            }, "aat-stdout-reader");
            Thread stderrThread = new Thread(() -> {
                try (InputStream stream = process.getErrorStream()) {
                    stderrRef.set(slurp(stream));
                } catch (Exception ignored) {}
            }, "aat-stderr-reader");

            stdoutThread.start();
            stderrThread.start();

            boolean finished = process.waitFor(PROCESS_TIMEOUT.toSeconds(), TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(5, TimeUnit.SECONDS);
            }
            stdoutThread.join(3000);
            stderrThread.join(3000);

            String stdout = stdoutRef.get();
            String stderr = stderrRef.get();
            if (!finished) {
                return new ProcessResult(1, stdout,
                    (stderr + "\nTimed out after " + PROCESS_TIMEOUT.toSeconds() + " seconds").trim());
            }
            return new ProcessResult(process.exitValue(), stdout, stderr);
        } catch (IOException e) {
            return new ProcessResult(1, "", e.getMessage() == null ? "Process launch failed" : e.getMessage());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return new ProcessResult(1, "", "Execution interrupted.");
        }
    }

    private static String slurp(InputStream stream) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append(System.lineSeparator());
            }
            return sb.toString();
        }
    }

    private record ProcessResult(int exitCode, String stdout, String stderr) {}
}
