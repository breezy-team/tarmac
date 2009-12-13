'''Script handling package for Tarmac.

NOTE: This will replace tarmac.bin and provide all the functionalities that
tarmac.bin currently provides. spec=tarmac-0.3
'''
def main():
    '''Main script handler.'''
    from tarmac.bin2 import commands
    from tarmac.bin2.registry import CommandRegistry
    registry = CommandRegistry()
    registry.register_from_module(commands)
    registry.run()
