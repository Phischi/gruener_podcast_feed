# Go IMAP Email Client

A simple IMAP email client written in Go that allows you to read your emails from any IMAP server and get AI-powered analysis using ChatGPT.

## Features

- Connect to any IMAP server
- List all mailboxes
- View the last 100 messages in your inbox
- Display message details (sender, subject, date)
- Get AI-powered analysis of email content using ChatGPT

## Prerequisites

- Go 1.21 or later
- An email account with IMAP access enabled
- OpenAI API key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/email-connector.git
cd email-connector
```

2. Install dependencies:
```bash
go mod download
```

3. Create a `.env` file in the project root with the following variables:
```
EMAIL_USER=your.email@example.com
EMAIL_PASSWORD=your_password
EMAIL_SERVER=imap.example.com:993
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Run the program:
```bash
go run main.go
```

2. The server will start on port 8080. You can access the email endpoint at:
```
http://localhost:8080/email
```

The endpoint will return a JSON response containing:
- Email details (from, subject, date)
- Original email body
- AI-generated analysis of the email content

## Common IMAP Server Addresses

- Gmail: imap.gmail.com:993
- Outlook/Office365: outlook.office365.com:993
- Yahoo: imap.mail.yahoo.com:993

## Security Note

For Gmail users:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password instead of your regular password

## License

MIT 