import sys
from fabric import Connection, task
from invoke import Responder
from fabric.config import Config

PROJECT_NAME = 'kitty_reward'
PROJECT_ROOT = '~/codes'
PROJECT_PATH = f'{PROJECT_ROOT}/{PROJECT_NAME}'
REPO_URL = f'git@github.com:zealzel/{PROJECT_NAME}.git'
USER = 'zealzel'
HOST = '172.104.163.189'


def get_connection(ctx):
    try:
        with Connection(ctx.host, ctx.user, forward_agent=ctx.forward_agent) as conn:
            return conn
    except Exception as e:
        return None

@task
def development(ctx):
    ctx.user = USER
    ctx.host = HOST
    ctx.forward_agent = True


def exists(file, dir):
    return file in dir


@task
def pull(ctx, branch="master"):
    # check if ctx is Connection object or Context object
    # if Connection object then calling method from program
    # else calling directly from terminal
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)

    with conn.cd(PROJECT_PATH):
        conn.run("git pull origin {}".format(branch))


@task
def clone(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    with conn.cd(PROJECT_ROOT):
        ls_result = conn.run("ls").stdout
        ls_result = ls_result.split("\n")
        if exists(PROJECT_NAME, ls_result):
            print("project already exists")
            return
        conn.run("git clone {} {}".format(REPO_URL, PROJECT_NAME))


# deploy task
@task
def deploy(ctx):
    conn = get_connection(ctx)
    if conn is None:
        sys.exit("Failed to get connection")
    clone(conn)
    with conn.cd(PROJECT_PATH):
        #  print("checkout to dev branch...")
        #  checkout(conn, branch="dev")
        print("pulling latest code from dev branch...")
        pull(conn)
        #  print("migrating database....")
        #  migrate(conn)
        print("restarting the nginx...")
        restart(conn)
