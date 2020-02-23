from fabric import task

@task
def echo(ctx, message): # with arguments
    ''' === with positional argument ===
        fab echo --message some_message
    '''
    conn = get_connection(ctx)
    conn.run(f'echo {message}')
