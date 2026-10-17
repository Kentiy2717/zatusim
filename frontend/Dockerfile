# Этап 1: Сборка веб-версии Expo
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npx expo export --platform web

# Этап 2: Раздача статики через ультралегкий Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]