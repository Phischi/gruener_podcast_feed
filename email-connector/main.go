package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/emersion/go-imap"
	"github.com/emersion/go-imap/client"
	"github.com/emersion/go-message/mail"
	"github.com/joho/godotenv"
	openai "github.com/sashabaranov/go-openai"
)

var emailClient *client.Client
var openaiClient *openai.Client
var systemPrompt string

// stripHTML removes all HTML tags and normalizes whitespace
func stripHTML(content string) string {
	// Remove HTML tags
	re := regexp.MustCompile("<[^>]*>")
	content = re.ReplaceAllString(content, " ")

	// Replace multiple spaces and newlines with a single space
	re = regexp.MustCompile(`\s+`)
	content = re.ReplaceAllString(content, " ")

	return strings.TrimSpace(content)
}

func loadSystemPrompt() error {
	content, err := os.ReadFile("system_prompt.txt")
	if err != nil {
		return fmt.Errorf("error reading system prompt file: %v", err)
	}
	systemPrompt = strings.TrimSpace(string(content))
	return nil
}

// truncateText truncates text to approximately maxTokens tokens
func truncateText(text string, maxTokens int) string {
	// Rough estimate: 1 token ≈ 4 characters
	maxChars := maxTokens * 4
	if len(text) <= maxChars {
		return text
	}
	return text[:maxChars] + "..."
}

// sanitizeFilename converts a string to a valid filename
func sanitizeFilename(s string) string {
	// Replace spaces with underscores
	s = strings.ReplaceAll(s, " ", "_")
	// Remove any characters that aren't alphanumeric, underscore, or hyphen
	re := regexp.MustCompile(`[^a-zA-Z0-9_-]`)
	s = re.ReplaceAllString(s, "")
	return s
}

func processLatestEmail() error {
	// Select INBOX
	mbox, err := emailClient.Select("INBOX", false)
	if err != nil {
		return fmt.Errorf("error selecting mailbox: %v", err)
	}

	// Get the last 100 messages
	var from uint32 = 1
	if mbox.Messages > 100 {
		from = mbox.Messages - 100 + 1
	}
	to := mbox.Messages
	seqset := new(imap.SeqSet)
	seqset.AddRange(from, to)

	messages := make(chan *imap.Message, 100)
	done := make(chan error, 1)
	go func() {
		done <- emailClient.Fetch(seqset, []imap.FetchItem{
			imap.FetchEnvelope,
			imap.FetchBody,
			imap.FetchBodyStructure,
			imap.FetchFlags,
			imap.FetchInternalDate,
			imap.FetchRFC822,
		}, messages)
	}()

	// Find the first message with subject starting with '[gn]'
	var targetMsg *imap.Message
	for msg := range messages {
		if strings.HasPrefix(msg.Envelope.Subject, "[gn]") {
			targetMsg = msg
			break
		}
	}

	if err := <-done; err != nil {
		return fmt.Errorf("error fetching messages: %v", err)
	}

	if targetMsg == nil {
		return fmt.Errorf("no matching email found")
	}

	// Get the message body
	var section imap.BodySectionName
	bodyReader := targetMsg.GetBody(&section)
	if bodyReader == nil {
		return fmt.Errorf("could not get message body")
	}

	// Create a new mail reader
	mr, err := mail.CreateReader(bodyReader)
	if err != nil {
		return fmt.Errorf("error creating mail reader: %v", err)
	}

	// Read the message body
	var bodyText strings.Builder
	for {
		p, err := mr.NextPart()
		if err == io.EOF {
			break
		} else if err != nil {
			return fmt.Errorf("error reading message part: %v", err)
		}

		switch h := p.Header.(type) {
		case *mail.InlineHeader:
			// Get the content type
			contentType, _, err := h.ContentType()
			if err != nil {
				log.Printf("Warning: Could not get content type: %v", err)
				continue
			}

			// Read the body content
			b, err := io.ReadAll(p.Body)
			if err != nil {
				return fmt.Errorf("error reading body: %v", err)
			}

			content := string(b)
			if strings.Contains(contentType, "text/html") {
				// Strip HTML and normalize whitespace
				content = stripHTML(content)
			} else if strings.Contains(contentType, "text/plain") {
				// Just normalize whitespace for plain text
				content = strings.Join(strings.Fields(content), " ")
			}

			if content != "" {
				bodyText.WriteString(content)
				bodyText.WriteString(" ")
			}
		}
	}

	// Get the cleaned email body
	emailBody := strings.TrimSpace(bodyText.String())

	// Try with GPT-4 first, then fall back to GPT-3.5-turbo if needed
	models := []string{openai.GPT4, openai.GPT3Dot5Turbo}
	var chatResp openai.ChatCompletionResponse
	var apiErr error

	for _, model := range models {
		// Truncate the email body to avoid token limits
		// Reserve some tokens for the system prompt and response
		truncatedBody := truncateText(emailBody, 6000) // Leave room for system prompt and response

		chatResp, apiErr = openaiClient.CreateChatCompletion(
			context.Background(),
			openai.ChatCompletionRequest{
				Model: model,
				Messages: []openai.ChatCompletionMessage{
					{
						Role:    openai.ChatMessageRoleSystem,
						Content: systemPrompt,
					},
					{
						Role:    openai.ChatMessageRoleUser,
						Content: truncatedBody,
					},
				},
			},
		)

		if apiErr == nil {
			log.Printf("Successfully used model: %s", model)
			break
		}

		log.Printf("Error with model %s: %v", model, apiErr)
		if model == openai.GPT4 {
			log.Printf("Falling back to GPT-3.5-turbo...")
			continue
		}
	}

	if apiErr != nil {
		return fmt.Errorf("OpenAI API error: %v", apiErr)
	}

	if len(chatResp.Choices) == 0 {
		return fmt.Errorf("OpenAI API returned no choices")
	}

	// Create podcast_scripts directory if it doesn't exist
	if err := os.MkdirAll("podcast_scripts", 0755); err != nil {
		return fmt.Errorf("error creating podcast_scripts directory: %v", err)
	}

	// Create filename from subject
	filename := sanitizeFilename(targetMsg.Envelope.Subject) + ".txt"
	filepath := filepath.Join("podcast_scripts", filename)

	// Write the AI response to file
	if err := os.WriteFile(filepath, []byte(chatResp.Choices[0].Message.Content), 0644); err != nil {
		return fmt.Errorf("error writing response to file: %v", err)
	}

	log.Printf("Successfully saved AI response to %s", filepath)
	return nil
}

func main() {
	// Get email credentials from environment variables
	if err := godotenv.Load(); err != nil {
		log.Fatal("Error loading .env file")
	}
	email := os.Getenv("EMAIL_USER")
	password := os.Getenv("EMAIL_PASSWORD")
	server := os.Getenv("EMAIL_SERVER")
	openaiKey := os.Getenv("OPENAI_API_KEY")

	if email == "" || password == "" || server == "" || openaiKey == "" {
		log.Fatal("Please set EMAIL_USER, EMAIL_PASSWORD, EMAIL_SERVER, and OPENAI_API_KEY environment variables")
	}

	// Log the first few characters of the API key to verify it's loaded
	if len(openaiKey) > 8 {
		log.Printf("OpenAI API key loaded (starts with: %s...)", openaiKey[:8])
	} else {
		log.Printf("Warning: OpenAI API key seems too short")
	}

	// Load system prompt
	if err := loadSystemPrompt(); err != nil {
		log.Fatal(err)
	}

	// Initialize OpenAI client
	openaiClient = openai.NewClient(openaiKey)

	// Connect to server
	var err error
	emailClient, err = client.DialTLS(server, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer emailClient.Logout()

	// Login
	if err := emailClient.Login(email, password); err != nil {
		log.Fatal(err)
	}
	fmt.Println("Successfully logged in!")

	// Process the latest email
	if err := processLatestEmail(); err != nil {
		log.Fatal(err)
	}
}
