FROM python:3.10-slim

# Install Bun
RUN apt-get update && apt-get install -y curl unzip && \
  curl -fsSL https://bun.sh/install | bash && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.bun/bin:$PATH"

WORKDIR /app

# Install MCP server dependencies
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production

# Install jobspy dependencies
COPY jobspy/requirements.txt jobspy/requirements.txt
RUN pip install --no-cache-dir -r jobspy/requirements.txt

# Copy all code
# NOTE: Pass runtime config via environment variables (docker run -e / k8s Secret)
# Do NOT copy .env into the image — see .env.example for required variables
COPY . .

EXPOSE 9423

CMD ["bun", "src/index.js"]
