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

def parse_time(time_str):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M")

def build_workflow(tasks):
    if len(tasks) == 0:
        return []
    tasks_sorted = sorted(tasks, key=lambda x: parse_time(x["timestamp"]))
    transitions = {}
    for i in range(len(tasks_sorted) - 1):
        current=tasks_sorted[i]
        next_task=tasks_sorted[i + 1]
        from_action = current["action"]
        to_action = next_task["action"]
        t1=parse_time(current["timestamp"])
        t2=parse_time(next_task["timestamp"])
        gap = (t2 - t1).total_seconds() / 60
        key=(from_action, to_action)
        if key not in transitions:
            transitions[key] = {
                "count": 0,
                "total_time": 0
            }
        transitions[key]["count"] += 1
        transitions[key]["total_time"] += gap
    workflow = []
    for(from_a,to_a), data in transitions.items():
        avg_gap = data["total_time"] / data["count"]
        workflow.append({
            "from": from_a,
            "to": to_a,
            "count": data["count"],
            "avg_time_gap_min": round(avg_gap, 2)
        })
    return workflow

if __name__ == "__main__":
    file_path = "sample_chat.txt"

    tasks = extract_tasks_from_file(file_path)

    print("\nExtracted Tasks:\n")
    for t in tasks:
        print(t)

    print(f"\nTotal tasks extracted: {len(tasks)}")
    
    workflow= build_workflow(tasks)
    print("\n Workflow Transitions:\n")
    for w in workflow:
        print(w)