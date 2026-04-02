FROM python:3.10-slim

# Install Node.js and pnpm
RUN apt-get update && apt-get install -y curl && \
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  npm install -g pnpm && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install MCP server dependencies
COPY package*.json ./
RUN pnpm install --frozen-lockfile --prod

# Install jobspy dependencies
COPY jobspy/requirements.txt jobspy/requirements.txt
RUN pip install --no-cache-dir -r jobspy/requirements.txt

# Copy all code
# NOTE: Pass runtime config via environment variables (docker run -e / k8s Secret)
# Do NOT copy .env into the image — see .env.example for required variables
COPY . .

EXPOSE 9423

CMD ["pnpm", "start"]
