package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	amqp "github.com/rabbitmq/amqp091-go"
)

type WebhookPayload struct {
	Action  string `json:"action"`
	Comment struct {
		Body string `json:"body"`
	} `json:"comment"`
	Issue struct {
		Number      int `json:"number"`
		PullRequest any `json:"pull_request"`
	} `json:"issue"`
	Repository struct {
		FullName string `json:"full_name"`
	} `json:"repository"`
}

func main() {
	http.HandleFunc("/webhook", func(w http.ResponseWriter, r *http.Request) {
		var payload WebhookPayload
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, "Error parsing JSON", 400)
			return
		}

		if payload.Action == "created" && payload.Comment.Body == "/ai-review" {
			publishToRabbit(payload)
			log.Printf("PR %d queued", payload.Issue.Number)
			w.Write([]byte("Acknowledged"))
			return
		}

		w.Write([]byte("OK"))
	})

	log.Println("Dispatcher listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func publishToRabbit(p WebhookPayload) {
	conn, _ := amqp.Dial(os.Getenv("RABBIT_URL"))
	defer conn.Close()

	ch, _ := conn.Channel()
	q, _ := ch.QueueDeclare("tasks", true, false, false, false, nil)
	body, _ := json.Marshal(p)

	ch.Publish("", q.Name, false, false, amqp.Publishing{ContentType: "application/json", Body: body})
}
