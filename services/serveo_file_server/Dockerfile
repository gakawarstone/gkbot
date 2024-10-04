FROM golang:1.23.1-alpine as builder

WORKDIR /app

COPY go.mod ./

COPY . .

RUN go build -o file-server .


FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/file-server .
RUN apk add --no-cache openssh

CMD ["./file-server"]

