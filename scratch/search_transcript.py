import json

transcript_path = r"C:\Users\nicks\.gemini\antigravity\brain\36ff5ea1-2d51-491c-b94f-4df85c074d1c\.system_generated\logs\transcript.jsonl"

def main():
    matches = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                step = json.loads(line)
                content = str(step.get("content", ""))
                tool_calls = str(step.get("tool_calls", ""))
                if "ssh" in content.lower() or "ssh" in tool_calls.lower() or "timeout" in content.lower() or "timeout" in tool_calls.lower():
                    matches.append((step.get("step_index"), step.get("type"), content[:100], tool_calls[:100]))
            except Exception as e:
                pass
                
    print(f"Found {len(matches)} matching steps.")
    print("Last 30 matches:")
    for m in matches[-30:]:
        print(f"Step {m[0]} ({m[1]}): content={m[2]}... tool_calls={m[3]}...")

if __name__ == "__main__":
    main()
