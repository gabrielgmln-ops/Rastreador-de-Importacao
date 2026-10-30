# rastreador-importacao/frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
EXPOSE 5173
# --host expõe o servidor do Vite fora do container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
