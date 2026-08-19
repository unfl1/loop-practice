"""Entry point for the Loop Engineering demo.

The actual iteration runner will be added later. After the loop finishes,
the presentation deck is rebuilt from the latest outputs/run_* directory.
"""

from scripts.build_presentation import build_presentation


def run_loop() -> None:
    """Placeholder for the future Loop execution logic."""


def main() -> None:
    try:
        run_loop()
    finally:
        build_presentation()


if __name__ == "__main__":
    main()
