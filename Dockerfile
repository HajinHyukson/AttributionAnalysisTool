# ---- Stage 1: Build Vue frontend ----
FROM node:20-alpine AS frontend
WORKDIR /app/java-web/frontend
COPY java-web/frontend/package.json java-web/frontend/package-lock.json* ./
RUN npm install
COPY java-web/frontend/ ./
RUN npm run build

# ---- Stage 2: Build Java backend ----
FROM maven:3.9-eclipse-temurin-17 AS backend
WORKDIR /app
COPY java-web/pom.xml java-web/pom.xml
RUN mvn -f java-web/pom.xml dependency:go-offline -q
COPY java-web/src java-web/src
COPY --from=frontend /app/java-web/src/main/resources/static/vue java-web/src/main/resources/static/vue
RUN mvn -f java-web/pom.xml package -DskipTests -q

# ---- Stage 3: Runtime ----
FROM eclipse-temurin:17-jre

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN python3 -m venv /app/.venv && /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Python analytics engine
COPY src/ src/

# Java JAR
COPY --from=backend /app/java-web/target/*.jar app.jar

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8082

EXPOSE 8082

CMD ["java", "-jar", "app.jar"]
