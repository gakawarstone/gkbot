package main

import (
	"bufio"
	"context"
	"errors"
	"fmt"
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
