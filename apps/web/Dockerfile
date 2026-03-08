FROM node:20-alpine
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
