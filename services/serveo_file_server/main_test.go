package main

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestReadServeoURL(t *testing.T) {
	for _, test := range []struct {
		name, output, want string
	}{
		{"serveo", "banner\nForwarding HTTP traffic from https://example.serveo.net\n", "https://example.serveo.net"},
		{"usercontent", "Forwarding http://example.serveousercontent.com\n", "http://example.serveousercontent.com"},
		{"missing", "https://example.com\n", ""},
	} {
		t.Run(test.name, func(t *testing.T) {
			got, err := readServeoURL(bufio.NewScanner(strings.NewReader(test.output)))
			if got != test.want || (err != nil) != (test.want == "") {
				t.Fatalf("readServeoURL = %q, %v; want %q", got, err, test.want)
			}
		})
	}
	_, err := readServeoURL(bufio.NewScanner(strings.NewReader(strings.Repeat("x", 100000))))
	if err == nil || !strings.Contains(err.Error(), "read SSH output") {
		t.Fatalf("scanner failure was lost: %v", err)
	}
}

func TestHTTPServerServesFilesAndShutsDown(t *testing.T) {
	directory := t.TempDir()
	if err := os.WriteFile(filepath.Join(directory, "example.txt"), []byte("contents"), 0600); err != nil {
		t.Fatal(err)
	}
	server, done, err := startHTTPServer(directory, 0)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = server.Close() })
	_, port, err := net.SplitHostPort(server.Addr)
	if err != nil {
		t.Fatal(err)
	}
	client := &http.Client{Timeout: time.Second}
	response, err := client.Get("http://127.0.0.1:" + port + "/example.txt")
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	body, err := io.ReadAll(response.Body)
	if err != nil || string(body) != "contents" || response.StatusCode != http.StatusOK {
		t.Fatalf("response = %d %q, %v", response.StatusCode, body, err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatalf("normal shutdown returned an error: %v", err)
	}
	if _, err := client.Get("http://127.0.0.1:" + port + "/example.txt"); err == nil {
		t.Fatal("HTTP listener is still accepting requests")
	}
}

func TestWriteURLToFile(t *testing.T) {
	directory := t.TempDir()
	if err := writeURLToFile("https://example.serveo.net", directory); err != nil {
		t.Fatal(err)
	}
	contents, err := os.ReadFile(filepath.Join(directory, "serveo_url"))
	if err != nil || string(contents) != "https://example.serveo.net" {
		t.Fatalf("URL file = %q, %v", contents, err)
	}
	if err := writeURLToFile("url", filepath.Join(directory, "missing")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("write error was lost: %v", err)
	}
}

func helperCommand(ctx context.Context, mode string) *exec.Cmd {
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestSSHHelperProcess$")
	command.Env = append(os.Environ(), "GK_SERVEO_HELPER="+mode)
	return command
}

func TestSSHHelperProcess(t *testing.T) {
	mode := os.Getenv("GK_SERVEO_HELPER")
	if mode == "" {
		return
	}
	if mode != "silent" {
		fmt.Println("Forwarding HTTP traffic from https://example.serveo.net")
	}
	if mode == "exit" {
		return
	}
	for {
		time.Sleep(time.Hour)
	}
}

func TestTunnelStartupFailures(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 150*time.Millisecond)
	defer cancel()
	if _, err := startTunnelCommand(helperCommand(ctx, "silent")); err == nil {
		t.Fatal("cancelled startup should fail without a URL")
	}
	command := exec.Command(filepath.Join(t.TempDir(), "missing-ssh"))
	if _, err := startTunnelCommand(command); err == nil {
		t.Fatal("missing SSH executable should fail")
	}
}

func TestRunCleansUpTunnelAndURL(t *testing.T) {
	for _, mode := range []string{"ready", "exit", "write-error"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			directory := t.TempDir()
			if mode == "write-error" {
				if err := os.Mkdir(filepath.Join(directory, "serveo_url"), 0700); err != nil {
					t.Fatal(err)
				}
			}
			var tunnel *sshTunnel
			start := func(ctx context.Context, port int) (*sshTunnel, error) {
				childMode := "ready"
				if mode == "exit" {
					childMode = "exit"
				}
				var err error
				tunnel, err = startTunnelCommand(helperCommand(ctx, childMode))
				if mode == "ready" {
					cancel()
				}
				return tunnel, err
			}
			err := run(ctx, directory, 0, start)
			if (err != nil) != (mode != "ready") {
				t.Fatalf("run = %v for mode %q", err, mode)
			}
			if tunnel == nil || tunnel.command.ProcessState == nil {
				t.Fatal("SSH process was not reaped")
			}
			if mode != "write-error" {
				if _, err := os.Stat(filepath.Join(directory, "serveo_url")); !errors.Is(err, os.ErrNotExist) {
					t.Fatalf("stale URL remains after shutdown: %v", err)
				}
			}
		})
	}
}

func TestRunRejectsInvalidDirectory(t *testing.T) {
	start := func(context.Context, int) (*sshTunnel, error) {
		t.Fatal("SSH must not start for invalid input")
		return nil, nil
	}
	directory := t.TempDir()
	file := filepath.Join(directory, "file")
	if err := os.WriteFile(file, nil, 0600); err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{file, filepath.Join(directory, "missing")} {
		if err := run(context.Background(), path, 0, start); err == nil {
			t.Fatalf("run accepted invalid directory %q", path)
		}
	}
}
