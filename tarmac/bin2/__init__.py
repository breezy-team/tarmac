'''Script handling package for Tarmac.

NOTE: This will replace tarmac.bin and provide all the functionalities that
tarmac.bin currently provides. spec=tarmac-0.3
'''
def main():
    '''Main script handler.'''
    from tarmac.bin2.commands import AuthCommand, CommandRegistry
    registry = CommandRegistry()
    registry.register_command(AuthCommand())
    registry.run()
