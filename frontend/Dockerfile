# Multi-stage build for React frontend
FROM node:18-alpine AS builder

# Set working directory  
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build argument for API URL (can be overridden at build time)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build

# Test stage
FROM node:18-alpine AS test

# Set working directory  
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies including dev dependencies
RUN npm install

# Copy source code
COPY . .

# Default command for running tests
CMD ["npm", "test"]

# Production stage - Simple HTTP server (no nginx needed with Traefik)
FROM node:18-alpine AS production

# Set working directory
WORKDIR /app

# Copy the built application from builder stage
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -G appuser -u 1001

# Set correct permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check (simple check if http-server is responding)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider --timeout=3 http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start simple HTTP server to serve static files
CMD ["npx", "http-server", "/app/dist", "-p", "80", "--gzip"] 