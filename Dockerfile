FROM python:3.10-slim

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install MCP server dependencies
COPY package*.json ./
RUN npm ci --only=production

# Install jobspy dependencies
COPY jobspy/requirements.txt jobspy/requirements.txt
RUN pip install --no-cache-dir -r jobspy/requirements.txt

# Copy .env file
COPY .env .

# Copy all code
COPY . .

EXPOSE 9423

CMD ["npm", "start"]