"""
agent.py
────────
The conversational layer:
  • run_agentic_turn — one user-message → tool-calling loop → final reply
  • print_banner     — CLI status header
  • main             — interactive REPL entrypoint
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import TYPE_CHECKING

from .core_tools import load_user_data
from .prompt     import SYSTEM_PROMPT
from .registry   import TOOLS, dispatch_tool
from .stats      import _compute_composite_score, _get_value

if TYPE_CHECKING:
    from groq import Groq  # type-only import; never executed at runtime


# ─────────────────────────────────────────────────────────────────────────────
# AGENTIC LOOP
# ─────────────────────────────────────────────────────────────────────────────

def run_agentic_turn(client: "Groq", messages: list, user_data: dict, verbose: bool = True) -> str:
    while True:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )
        choice = response.choices[0]
        msg    = choice.message

        msg_dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id":       tc.id,
                    "type":     "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(msg_dict)

        if not msg.tool_calls:
            return msg.content or ""

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                fn_args = {}

            if verbose:
                args_str = ", ".join(f"{k}={v!r}" for k, v in fn_args.items()) if fn_args else ""
                print(f"  🔧 {fn_name}({args_str})")

            result_str = dispatch_tool(fn_name, fn_args, user_data)
            messages.append({
                "role":          "tool",
                "tool_call_id":  tc.id,
                "content":       result_str,
            })


# ─────────────────────────────────────────────────────────────────────────────
# BANNER & CLI MAIN
# ─────────────────────────────────────────────────────────────────────────────

def print_banner(user_data: dict):
    name   = user_data["personal_memory"]["name"]
    frames = user_data["wellbeing_frames"]
    weeks  = len(frames)
    latest = frames[-1] if frames else {}

    composite = _compute_composite_score(latest) if latest else None
    happy     = _get_value(latest, "emotions.happy_positive")   if latest else None
    anxious   = _get_value(latest, "emotions.anxious_worried")  if latest else None
    work      = _get_value(latest, "stresses.work_academic")    if latest else None

    print("\n" + "═" * 70)
    print("   🧠  Mental Health Counselor — Analytics-Enhanced (Groq)")
    print("═" * 70)
    print(f"   User: {name}, {user_data['personal_memory'].get('age', '?')}y")
    print(f"   Data: {weeks} weeks tracked")
    if composite is not None:
        print(f"   Wellbeing score (latest): {composite}/100")
    if happy is not None:
        print(f"   Happy/positive: {happy}/5    Anxious/worried: {anxious}/5    Work stress: {work}/5")
    print("═" * 70)
    print("   Available tools: 5 core + 12 analytics")
    print("   Tool calls shown with 🔧 (use --quiet to hide)")
    print("   Type 'quit' to exit.\n")


def main():
    parser = argparse.ArgumentParser(description="Mental Health Counselor (Groq) with Analytics")
    parser.add_argument("--data",  default="data3.json",            help="Path to user data JSON")
    parser.add_argument("--quiet", action="store_true",             help="Hide tool calls")
    parser.add_argument("--model", default="llama-3.3-70b-versatile", help="Groq model")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"Error: data file '{args.data}' not found.")
        sys.exit(1)

    user_data = load_user_data(args.data)

    api_key = "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"
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set.")
        sys.exit(1)

    from groq import Groq  # imported lazily so the package loads without groq installed
    client = Groq(api_key=api_key)

    print_banner(user_data)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTake care. Goodbye! 🌿")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\nTake care of yourself. Goodbye! 🌿")
            break

        messages.append({"role": "user", "content": user_input})

        print("\nCounselor (thinking...):")
        reply = run_agentic_turn(client, messages, user_data, verbose=not args.quiet)
        print(f"\nCounselor: {reply}\n")


if __name__ == "__main__":
    main()
