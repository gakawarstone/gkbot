package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

const uploadPath = "/files"

type Task struct {
	URL string `json:"url"`
	Id  string `json:"id"`
}

func main() {
	// Ensure the upload directory exists
	if err := os.MkdirAll(uploadPath, os.ModePerm); err != nil {
		panic(fmt.Sprintf("Failed to create upload directory: %v", err))
	}

	http.HandleFunc("/upload", uploadHandler)
	http.HandleFunc("/fetch", fetchHandler)

	fmt.Println("Server started on http://localhost:8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(fmt.Sprintf("Server failed: %v", err))
	}
}

// uploadHandler handles the video upload logic
func uploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	// Parse the multipart form
	if err := r.ParseMultipartForm(0); err != nil { // No max size limit
		http.Error(w, "Unable to parse form", http.StatusBadRequest)
		return
	}

	id := r.FormValue("id")
	if id == "" {
		http.Error(w, "ID is required", http.StatusBadRequest)
		return
	}

	// Retrieve the file
	file, header, err := r.FormFile("video")
	if err != nil {
		http.Error(w, "Error retrieving the file", http.StatusInternalServerError)
		return
	}
	defer file.Close()

	// Validate file type (basic validation)
	// if header.Header.Get("Content-Type")[:5] != "video/webm" {
	// 	http.Error(w, "Only video files are allowed", http.StatusBadRequest)
	// 	return
	// }

	// Create a new file in the uploads directory
	filePath := filepath.Join(uploadPath, id, header.Filename)
	destFile, err := os.Create(filePath)
	if err != nil {
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}
	defer destFile.Close()

	// Copy the uploaded file to the destination
	if _, err := io.Copy(destFile, file); err != nil {
		http.Error(w, "Failed to copy file content", http.StatusInternalServerError)
		return
	}

	// Respond to the client
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	response := map[string]string{
		"message":  "File uploaded successfully",
		"filename": header.Filename,
	}
	json.NewEncoder(w).Encode(response)
}

func fetchHandler(w http.ResponseWriter, r *http.Request) {
	var tasks []Task

	// tasks = append(tasks, Task{URL: "https://youtube.com/shorts/txzQarZFz_A?si=-cIYDngJBM88HXvZ"})
	// tasks = append(tasks, Task{URL: "https://youtube.com/shorts/81O0eJjPlkk?si=ps7Vz02ADDyYRCmj"})

	file, err := os.Open("/files/tasks")
	if err != nil {
		http.Error(w, "Failed to open file with links", http.StatusInternalServerError)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for scanner.Scan() {
		line := scanner.Text()
		fmt.Println(line)
		// Split into URL and ID, allowing commas in the URL
		parts := strings.SplitN(line, ",", 2)
		fmt.Println(parts)
		url := strings.TrimSpace(parts[0])
		id := strings.TrimSpace(parts[1])
		tasks = append(tasks, Task{URL: url, Id: id})
	}

	if err := scanner.Err(); err != nil {
		http.Error(w, "Failed to scan file with links", http.StatusInternalServerError)
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(
		struct {
			Tasks []Task `json:"tasks"`
		}{
			tasks,
		},
	)

}
