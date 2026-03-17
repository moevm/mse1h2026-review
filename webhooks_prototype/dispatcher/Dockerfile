FROM golang:1.25-alpine AS builder

RUN apk add --no-cache git

WORKDIR /app

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN go build -o main .


FROM alpine:3.19

RUN adduser -D appuser

WORKDIR /app

COPY --from=builder /app/main .

USER appuser

CMD ["./main"]