FROM node:20-alpine

RUN adduser -D appuser

WORKDIR /app

COPY app/package.json app/package-lock.json* ./

RUN npm install

COPY app/ ./

RUN npm run build

USER appuser

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]