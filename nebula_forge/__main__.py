"""
NEBULA-FORGE — Entry Point
Run: python -m nebula_forge  OR  nebula-forge
"""

from .app import NebulaApp


def main():
    app = NebulaApp()
    app.run()


if __name__ == "__main__":
    main()
