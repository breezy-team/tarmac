'''Script handling package for Tarmac.

NOTE: This will replace tarmac.bin and provide all the functionalities that
tarmac.bin currently provides.
'''


def main():
    '''Main script handler.'''
    import sys

    from breezy import ui

    from tarmac.bin import commands
    from tarmac.bin.registry import CommandRegistry

    ui.ui_factory = ui.make_ui_for_terminal(
        sys.stdin, sys.stdout, sys.stderr)

    registry = CommandRegistry()
    registry.install_hooks()
    registry.register_from_module(commands)

    # I hate that args have to be handled here, instead of in CommandRegistry,
    # but otherwise the tests for CommandRegistry.run try and use tarmac.tests
    # as the command to run.  :/
    args = sys.argv[1:]
    if not args:
        args = ['help']
    registry.run(args)
