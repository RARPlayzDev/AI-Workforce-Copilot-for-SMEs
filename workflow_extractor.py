from datetime import datetime

ACTION_KEYWORDS = [
    "sent",
    "approved",
    "received",
    "delivered",
    "reviewed",
    "assigned",
    "confirmed",
    "invoice",
    "payment",
    "refund",
    "completed",
    "initiated"
]


def parse_whatsapp_line(line):
    try:
        if " - " not in line:
            return None

        date_part, message_part = line.split(" - ", 1)

        timestamp = datetime.strptime(date_part, "%d/%m/%Y, %H:%M")

        if ":" not in message_part:
            return None

        actor, message = message_part.split(":", 1)

        return {
            "timestamp": timestamp,
            "actor": actor.strip(),
            "message": message.strip()
        }

    except Exception as e:
        print("Parse error:", e)
        return None


def detect_action(message):
    message_lower = message.lower()

    for keyword in ACTION_KEYWORDS:
        if keyword in message_lower:
            return keyword

    return None


def create_task(parsed_line):
    action = detect_action(parsed_line["message"])

    if action is None:
        return None

    return {
        "actor": parsed_line["actor"],
        "action": action,
        "timestamp": parsed_line["timestamp"].strftime("%Y-%m-%d %H:%M"),
        "raw_text": parsed_line["message"]
    }


def extract_tasks_from_file(file_path):
    tasks = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            parsed = parse_whatsapp_line(line)

            if parsed:
                task = create_task(parsed)

                if task:
                    tasks.append(task)

    return tasks


if __name__ == "__main__":
    file_path = "sample_chat.txt"

    tasks = extract_tasks_from_file(file_path)

    print("\nExtracted Tasks:\n")
    for t in tasks:
        print(t)

    print(f"\nTotal tasks extracted: {len(tasks)}")