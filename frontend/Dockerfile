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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start simple HTTP server to serve static files
CMD ["npx", "http-server", "-p", "80", "-d", "/app/dist", "--gzip"] 