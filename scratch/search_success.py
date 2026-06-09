import json

transcript_path = r"C:\Users\nicks\.gemini\antigravity\brain\36ff5ea1-2d51-491c-b94f-4df85c074d1c\.system_generated\logs\transcript.jsonl"

def main():
    steps = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
                
    for i, s in enumerate(steps):
        # Look for run_command tool calls
        if s.get("type") == "PLANNER_RESPONSE" and "tool_calls" in s:
            t_calls = s["tool_calls"]
            for tc in t_calls:
                if tc.get("name") == "run_command":
                    cmd_line = tc.get("args", {}).get("CommandLine", "")
                    if "ssh" in cmd_line.lower() or "scp" in cmd_line.lower():
                        # Find the corresponding output step (usually the next step or a few steps later)
                        # We match by step_index or search forward
                        found_out = False
                        for j in range(i+1, min(i+5, len(steps))):
                            out_step = steps[j]
                            if out_step.get("type") in ["RUN_COMMAND", "SYSTEM_MESSAGE"] and "Output:" in out_step.get("content", ""):
                                content = out_step["content"]
                                print(f"Step {s.get('step_index')} -> {out_step.get('step_index')}: {cmd_line[:80]}...")
                                if "completed successfully" in content:
                                    print("  RESULT: SUCCESS")
                                else:
                                    print("  RESULT: FAILED/TIMEOUT")
                                found_out = True
                                break

if __name__ == "__main__":
    main()
