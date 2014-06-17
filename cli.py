#!/usr/bin/python3
import minestorm.cli

cli = minestorm.cli.CommandsManager()
# Register commands
cli.register( minestorm.cli.StartCommand() )
cli.register( minestorm.cli.ConsoleCommand() )
cli.register( minestorm.cli.StatusCommand() )

cli.route()