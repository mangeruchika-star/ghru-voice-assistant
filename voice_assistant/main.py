"""CLI entry point for the voice assistant."""

from __future__ import annotations

import argparse

from .assistant import AssistantConfig, CollegeVoiceAssistant
from .data import RESPONSES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="College voice assistant with speech and keyboard fallback."
    )
    parser.add_argument(
        "--language",
        choices=sorted(RESPONSES.keys()),
        default="en",
        help="Default assistant language.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Assistant display name.",
    )
    parser.add_argument(
        "--no-voice-input",
        action="store_true",
        help="Disable microphone input and use keyboard input only.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    assistant_name = args.name or RESPONSES[args.language]["assistant_name"]
    assistant = CollegeVoiceAssistant(
        AssistantConfig(
            assistant_name=assistant_name,
            language=args.language,
            use_voice_input=not args.no_voice_input,
        )
    )
    return assistant.run()


if __name__ == "__main__":
    raise SystemExit(main())
