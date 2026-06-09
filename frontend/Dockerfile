FROM node:20-alpine

WORKDIR /app

# Install system dependencies and node packages
COPY package.json package-lock.json ./
RUN apk add --no-cache libc6-compat && npm ci

# Copy codebase and compile
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS="--max-old-space-size=512"
RUN npm run build

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application using Next.js production server
CMD ["npx", "next", "start"]
