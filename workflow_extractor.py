from datetime import datetime
from collections import Counter
import json


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

def detect_bottlenecks(workflow):
    if not workflow:
        return []

    total = sum(w["avg_time_gap_min"] for w in workflow)
    overall_avg = total / len(workflow)

    bottlenecks = []

    for w in workflow:
        if w["avg_time_gap_min"] > overall_avg:
            bottlenecks.append({
                "step": f"{w['from']} → {w['to']}",
                "avg_delay": w["avg_time_gap_min"],
                "issue": "High delay compared to process average"
            })

    return bottlenecks

def detect_loops(tasks):
    if not tasks:
        return []
    
    loops = []
    visited = set()
    
    for i in range(len(tasks)):
        current_action = tasks[i]["action"]
        
        for j in range(i + 1, len(tasks)):
            if tasks[j]["action"] == current_action and current_action in visited:
                loops.append((current_action, i, j))
            visited.add(tasks[j]["action"])
    
    return loops

def calculate_loop_penalty(tasks):
    loops = detect_loops(tasks)

    if not loops:
        return 0

    penalty = len(loops) * 10
    return penalty

def calculate_delay_penalty(workflow):
    if not workflow:
        return 0

    total_delay = sum(w["avg_time_gap_min"] for w in workflow)
    avg_delay = total_delay / len(workflow)

    if avg_delay < 30:
        return 5
    elif avg_delay < 60:
        return 15
    else:
        return 25

def calculate_efficiency_score(tasks, workflow):
    base_score = 100

    loop_penalty = calculate_loop_penalty(tasks)
    delay_penalty = calculate_delay_penalty(workflow)

    final_score = base_score - (loop_penalty + delay_penalty)

    if final_score < 0:
        final_score = 0

    return {
        "efficiency_score": final_score,
        "loop_penalty": loop_penalty,
        "delay_penalty": delay_penalty
    }

def generate_kpi_summary(tasks, workflow):
    total_steps = len(tasks)
    unique_steps = len(set(task["action"] for task in tasks))

    total_transitions = sum(w["count"] for w in workflow)

    avg_delay = 0
    if workflow:
        avg_delay = sum(w["avg_time_gap_min"] for w in workflow) / len(workflow)

    return {
        "total_steps": total_steps,
        "unique_steps": unique_steps,
        "total_transitions": total_transitions,
        "average_delay_minutes": round(avg_delay, 2)
    }

def classify_delay_risk(avg_delay):
    if avg_delay < 30:
        return "Low"
    elif avg_delay < 60:
        return "Medium"
    else:
        return "High"
    
def add_risk_levels(workflow):
    for w in workflow:
        w["risk_level"] = classify_delay_risk(w["avg_time_gap_min"])
    return workflow

def get_step_criticality(tasks, workflow):
    freq = Counter(task["action"] for task in tasks)

    delay_map = {}

    for w in workflow:
        delay_map[w["from"]] = delay_map.get(w["from"], 0) + w["avg_time_gap_min"]

    critical_steps = []

    for step, count in freq.items():
        delay = delay_map.get(step, 0)

        score = count * delay

        critical_steps.append({
            "step": step,
            "frequency": count,
            "delay_impact": round(delay, 2),
            "criticality_score": round(score, 2)
        })

    critical_steps.sort(key=lambda x: x["criticality_score"], reverse=True)

    return critical_steps

def analyze_workflow(file_path):
    # Step 1
    tasks = extract_tasks_from_file(file_path)

    # Step 2
    workflow = build_workflow(tasks)

    # Step 3
    workflow = add_risk_levels(workflow)

    # Step 4
    bottlenecks = detect_bottlenecks(workflow)

    # Step 5
    kpis = generate_kpi_summary(tasks, workflow)

    # Step 6
    efficiency = calculate_efficiency_score(tasks, workflow)

    # Step 7
    critical_steps = get_step_criticality(tasks, workflow)

    # Step 8
    loops = detect_loops(tasks)

    return {
        "tasks": tasks,
        "workflow": workflow,
        "bottlenecks": bottlenecks,
        "loops": loops,
        "kpis": kpis,
        "efficiency": efficiency,
        "critical_steps": critical_steps
    }

if __name__ == "__main__":
    file_path = "sample_chat.txt"

    result = analyze_workflow(file_path)

    print("\n--- FULL ANALYSIS ---\n")
    print(json.dumps(result, indent=2))
"""if __name__ == "__main__":
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
    
    print("\n--- BOTTLENECKS ---")
    bottlenecks = detect_bottlenecks(workflow)
    for b in bottlenecks:
        print(b)

    print("\n--- KPI SUMMARY ---")
    kpis = generate_kpi_summary(tasks, workflow)
    print(kpis)

    print("\n--- EFFICIENCY SCORE ---")
    efficiency = calculate_efficiency_score(tasks, workflow)
    print(efficiency)"""