FROM golang:1.23.1-alpine as builder

WORKDIR /app

COPY . .

RUN go build -o ytdlp_workers_supervisor main.go


FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/ytdlp_workers_supervisor  .

CMD ["./ytdlp_workers_supervisor"]

