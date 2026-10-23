"""Allow the installed package to be invoked with python -m silo."""

from silo.cli.main import main

raise SystemExit(main())
