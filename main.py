"""
Main entry point for Survival AI.
Can run in terminal mode or launch web interface.
"""

import sys
import argparse
from agent.brain import SurvivalBrain
from interface.speech import SpeechInput
from interface.display import Display
from interface.messaging import MeshMessaging


def main():
    parser = argparse.ArgumentParser(description="Survival AI")
    parser.add_argument("--mode", choices=["terminal", "web"], default="terminal")
    parser.add_argument("--web-port", type=int, default=5000)
    args = parser.parse_args()

    if args.mode == "web":
        from web_app import app
        print("Starting web interface...")
        app.run(host="0.0.0.0", port=args.web_port)
        return

    # Terminal mode
    print("=== SURVIVAL AI ===")
    print("Offline survival assistant. Type 'quit' to exit.")
    print("Commands: :speak (voice input), :map, :messages, :help\n")

    brain = SurvivalBrain()
    display = Display(DISPLAY_MODE="terminal")
    speech = SpeechInput()
    messaging = MeshMessaging()

    print(f"System check: {brain.check_systems()}")

    while True:
        try:
            user_input = input("> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if user_input == ":speak":
                print("Listening...")
                text = speech.listen(timeout=5)
                if text:
                    user_input = text
                    print(f"You: {user_input}")
                else:
                    print("No speech detected")
                    continue

            if user_input == ":messages":
                msgs = messaging.get_messages()
                for m in msgs[:10]:
                    print(f"[{m.get('from')}] {m.get('message')}")
                continue

            if user_input == ":help":
                print("Commands:")
                print("  :speak    - Voice input")
                print("  :messages - View mesh messages")
                print("  :help     - Show this help")
                print("  quit      - Exit")
                continue

            # Get sources
            sources = brain.get_sources(user_input)

            # Generate response
            response = brain.process(user_input)

            # Display with sources
            display.show(response, sources[0]["source"] if sources else None)

            # Show sources
            if sources:
                print("\nSources:")
                for s in sources:
                    print(f"  - {s.get('source', 'Unknown')}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nExiting...")


if __name__ == "__main__":
    main()