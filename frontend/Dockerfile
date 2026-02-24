FROM node:20-alpine3.23 AS builder

WORKDIR /app

COPY app/package.json app/package-lock.json* ./

RUN npm install

COPY app/ ./

RUN npm run build


FROM nginx:1.28.2-alpine3.23

WORKDIR /usr/share/nginx/html

RUN rm -rf ./*

COPY --from=builder app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]