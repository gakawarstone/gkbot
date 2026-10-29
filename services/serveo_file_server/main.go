package main

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"regexp"
	"syscall"
	"time"
)

var serveoURLPattern = regexp.MustCompile(`https?://[a-zA-Z0-9-]+\.(?:serveo\.net|serveousercontent\.com)(?:/|\b)`)

func startHTTPServer(directory string, port int) (*http.Server, <-chan error, error) {
	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		return nil, nil, err
	}
	server := &http.Server{
		Addr:              listener.Addr().String(),
		Handler:           http.FileServer(http.Dir(directory)),
		ReadHeaderTimeout: 10 * time.Second,
	}
	done := make(chan error, 1)
	go func() {
		err := server.Serve(listener)
		if errors.Is(err, http.ErrServerClosed) {
			err = nil
		}
		done <- err
	}()
	return server, done, nil
}

type sshTunnel struct {
	command *exec.Cmd
	url     string
	done    chan struct{}
	err     error
}

func readServeoURL(scanner *bufio.Scanner) (string, error) {
	for scanner.Scan() {
		if url := serveoURLPattern.FindString(scanner.Text()); url != "" {
			return url, nil
		}
	}
	if err := scanner.Err(); err != nil {
		return "", fmt.Errorf("read SSH output: %w", err)
	}
	return "", errors.New("SSH tunnel exited without a Serveo URL")
}

func startTunnelCommand(command *exec.Cmd) (*sshTunnel, error) {
	stdout, err := command.StdoutPipe()
	if err != nil {
		return nil, err
	}
	command.Stderr = os.Stderr
	if err := command.Start(); err != nil {
		return nil, err
	}
	scanner := bufio.NewScanner(stdout)
	url, err := readServeoURL(scanner)
	if err != nil {
		_ = command.Process.Kill()
		_ = command.Wait()
		return nil, err
	}
	tunnel := &sshTunnel{command: command, url: url, done: make(chan struct{})}
	go func() {
		// Drain output before Wait closes the pipe, including scanner-buffered data.
		for scanner.Scan() {
		}
		tunnel.err = command.Wait()
		if err := scanner.Err(); err != nil {
			tunnel.err = fmt.Errorf("read SSH output: %w", err)
		}
		close(tunnel.done)
	}()
	return tunnel, nil
}

func startSSHTunnel(ctx context.Context, port int) (*sshTunnel, error) {
	command := exec.CommandContext(ctx, "ssh", "-o", "StrictHostKeyChecking=no",
		"-o", "ExitOnForwardFailure=yes", "-R", fmt.Sprintf("80:localhost:%d", port), "serveo.net")
	return startTunnelCommand(command)
}

func (tunnel *sshTunnel) stop() {
	_ = tunnel.command.Process.Kill()
	<-tunnel.done
}

func writeURLToFile(serveoURL, directory string) error {
	filePath := filepath.Join(directory, "serveo_url")
	if err := os.WriteFile(filePath, []byte(serveoURL), 0644); err != nil {
		return fmt.Errorf("write Serveo URL: %w", err)
	}
	return nil
}

type tunnelStarter func(context.Context, int) (*sshTunnel, error)

func run(ctx context.Context, directory string, port int, startTunnel tunnelStarter) error {
	info, err := os.Stat(directory)
	if err != nil {
		return fmt.Errorf("stat served directory: %w", err)
	}
	if !info.IsDir() {
		return fmt.Errorf("%s is not a directory", directory)
	}

	server, serverDone, err := startHTTPServer(directory, port)
	if err != nil {
		return fmt.Errorf("start HTTP server: %w", err)
	}
	defer func() {
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdownCtx); err != nil {
			_ = server.Close()
		}
	}()

	tunnel, err := startTunnel(ctx, port)
	if err != nil {
		if ctx.Err() != nil {
			return nil
		}
		return fmt.Errorf("start SSH tunnel: %w", err)
	}
	defer tunnel.stop()
	if err := writeURLToFile(tunnel.url, directory); err != nil {
		return err
	}
	defer os.Remove(filepath.Join(directory, "serveo_url"))
	fmt.Printf("Access the server at: %s\n", tunnel.url)

	select {
	case <-ctx.Done():
		return nil
	case err := <-serverDone:
		return fmt.Errorf("HTTP server stopped: %v", err)
	case <-tunnel.done:
		if ctx.Err() != nil {
			return nil
		}
		return fmt.Errorf("SSH tunnel stopped: %v", tunnel.err)
	}
}

func main() {
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	if err := run(ctx, "/files", 8089, startSSHTunnel); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
