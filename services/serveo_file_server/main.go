package main

import (
	"bufio"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
)

func startHTTPServer(directory string, port int) *http.Server {
	fs := http.FileServer(http.Dir(directory))

	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: fs,
	}

	go func() {
		fmt.Printf("Starting HTTP server to serve files from %s on port %d...\n", directory, port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Println("Failed to start HTTP server:", err)
		}
	}()

	return server
}

func startSSHTunnel(port int) (*exec.Cmd, string, error) {
	var sshCmd *exec.Cmd
	sshCmd = exec.Command("ssh", "-o", "StrictHostKeyChecking=no", "-R", fmt.Sprintf("80:localhost:%d", port), "serveo.net")

	stdout, err := sshCmd.StdoutPipe()
	if err != nil {
		return nil, "", err
	}
	if err := sshCmd.Start(); err != nil {
		return nil, "", err
	}

	scanner := bufio.NewScanner(stdout)
	var serveoURL string
	for scanner.Scan() {
		line := scanner.Text()
		re := regexp.MustCompile(`https?://[^\s]+(?:\.serveo\.net|\.serveousercontent\.com)`)
		if url := re.FindString(line); url != "" {
			serveoURL = url
			break
		}
	}

	return sshCmd, serveoURL, nil
}

func writeURLToFile(serveoURL, directory string) error {
	filePath := filepath.Join(directory, "serveo_url")
	err := os.WriteFile(filePath, []byte(serveoURL), 0644)
	if err != nil {
		return fmt.Errorf("failed to write to file: %v", err)
	}

	fmt.Printf("Serveo URL written to file: %s\n", filePath)
	return nil
}

func main() {
	directoryToServe := "/files" // Replace with the directory you want to serve
	port := 8089                 // Port for the HTTP server

	absPath, err := filepath.Abs(directoryToServe)
	if err != nil || !fileExists(absPath) {
		fmt.Printf("Directory %s does not exist.\n", absPath)
		return
	}

	httpServer := startHTTPServer(directoryToServe, port)

	fmt.Println("Creating SSH tunnel through serveo.net...")
	sshTunnel, serveoURL, err := startSSHTunnel(port)
	if err != nil {
		fmt.Println("Failed to start SSH tunnel:", err)
		return
	}
	defer sshTunnel.Process.Kill()

	if serveoURL != "" {
		fmt.Printf("Access the server at: %s\n", serveoURL)
		err := writeURLToFile(serveoURL, absPath)
		if err != nil {
			fmt.Println("Error writing Serveo URL to file:", err)
		}
	}

	select {}

	if err := httpServer.Close(); err != nil {
		fmt.Println("Error shutting down HTTP server:", err)
	}

	fmt.Println("HTTP server and SSH tunnel closed.")
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return !os.IsNotExist(err)
}
