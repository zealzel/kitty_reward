import sys
from textwrap import dedent
from fabric import Connection, task
import invoke
from fabric.config import Config

PROJECT_NAME = 'kitty_reward'
PROJECT_ROOT = '~/codes'
HOME = '~/'
PROJECT_PATH = f'{PROJECT_ROOT}/{PROJECT_NAME}'
REPO_URL = f'https://github.com/zealzel/{PROJECT_NAME}.git'
LOCAL_USER = 'zealzel'
FILE_RC = f'{HOME}/.bash_profile'


PYTHON_VER = '3.7.0'
VIRTUALENV_NAME = PROJECT_NAME


''' ssh comamand examples to access vagrant boxes
ssh ubuntu@127.0.0.1 -p 2200 -i /Users/zealzel/vagrant_machines/xenial64/.vagrant/machines/default/virtualbox/private_key
-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o IdentitiesOnly=yes
'''

@task
def xenial(ctx):
    ctx.user = 'ubuntu'
    ctx.vagrant_box = 'xenial64'
    ctx.host = '127.0.0.1'
    ctx.port = '2200'
    ctx.key = f'/Users/{LOCAL_USER}/vagrant_machines/{ctx.vagrant_box}/.vagrant/machines/default/virtualbox/private_key'
    ctx.forward_agent = True


@task
def linode(ctx):
    ctx.user = 'zealzel'
    ctx.vagrant_box = None
    ctx.host = '172.104.163.189'
    ctx.port = None
    ctx.key = None
    ctx.forward_agent = True


def defined_kwargs(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


def get_connection(ctx):
    if isinstance(ctx, Connection):
        return ctx
    else:
        try:
            with Connection(
                **defined_kwargs(
                    host=ctx.host,
                    user=ctx.user,
                    port=ctx.port,
                    connect_kwargs={"key_filename": ctx.key},
                    inline_ssh_env=True,
                    forward_agent=ctx.forward_agent)
                ) as conn:
                return conn
        except Exception as e:
            return None


@task
def ls(ctx):
    conn = get_connection(ctx)
    conn.run('ls -al')


@task
def provision(ctx):
    conn = get_connection(ctx)
    package_update(conn)
    download_pip(conn)
    pyenv(conn)


@task
def package_update(ctx):
    conn = get_connection(ctx)
    conn.run('sudo apt update')


@task
def appends_test(ctx):
    conn = get_connection(ctx)
    file = '~/.bash_profile'

    # test1: single line
    content1 = 'export PATH=$HOME/.local/bin:$PATH'

    # test2: multiple lines
    content2 = dedent('''
    if command -v pyenv 1>/dev/null 2>&1; then
      eval "$(pyenv init -)"
    fi
    ''').strip()

    appends(conn, file, content1)
    appends(conn, file, content2)


def appends(conn, file, lines):
    conn.run(f"echo -e '{lines}' >> ~/.bash_profile")


@task
def download_pip(ctx):
    ''' === underscore is replaced with hyphens ===
        fab download-pip
    '''
    url = 'https://bootstrap.pypa.io/get-pip.py'
    conn = get_connection(ctx)
    conn.run(f'curl {url} -o get-pip.py')

    '''
        copy pip binary into ~/.local/bin
    '''
    conn.run('python3 get-pip.py')



@task
def pyenv(ctx):
    conn = get_connection(ctx)

    '''
    Prerequisites for ubuntu
    reference: https://github.com/pyenv/pyenv/wiki/Common-build-problems
    '''
    conn.run('sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
              libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
              xz-utils tk-dev libffi-dev liblzma-dev python-openssl git')

    home = conn.run('echo $HOME').stdout.strip()
    path = conn.run('echo $PATH').stdout.strip()
    pyenv_root = f'{home}/.pyenv'

    with conn.cd(HOME):
        if conn.run('source ~/.bash_profile; pyenv --version', warn=True, hide=True).failed:
            print('pyenv not installed')

            '''
            pyenv respository at github
            https://github.com/pyenv/pyenv#locating-the-python-installation
            '''
            conn.run(f'git clone https://github.com/pyenv/pyenv.git {pyenv_root}', warn=True)
            content = dedent(f'''
            export PYENV_ROOT={pyenv_root}
            export PATH={pyenv_root}/bin:$PATH
            if command -v pyenv 1>/dev/null 2>&1; then
              eval "$(pyenv init -)"
            fi
            ''').strip()
            appends(conn, FILE_RC, content)


        print('pyenv installed. download pyenv-virtualenv')

        '''
        pyenv-virtualenv respository at github
        https://github.com/pyenv/pyenv-virtualenv
        '''
        conn.run('git clone https://github.com/pyenv/pyenv-virtualenv.git'
                 f' {pyenv_root}/plugins/pyenv-virtualenv', warn=True)
        conn.run(
            f'source {FILE_RC};'
            f'pyenv install {PYTHON_VER};'
            f'pyenv virtualenv {PYTHON_VER} {VIRTUALENV_NAME}'
        )


@task
def download_py_packages(ctx):
    conn = get_connection(ctx)
    with conn.cd(PROJECT_PATH):
        conn.run(
            f'source {FILE_RC};'
            f'pyenv activate {VIRTUALENV_NAME};'
            f'pip install -U pip;'
            f'pip install -r requirements.txt'
        )


@task
def echo(ctx, message): # with arguments
    ''' === with positional argument ===
        fab echo --message some_message
    '''
    conn = get_connection(ctx)
    conn.run(f'echo {message}')


def exists(file, dir):
    return file in dir


@task
def pull(ctx, branch="master"):
    conn = get_connection(ctx)
    with conn.cd(PROJECT_PATH):
        conn.run("git pull origin {}".format(branch))


@task
def clone(ctx):
    conn = get_connection(ctx)
    conn.run(f'mkdir -p {PROJECT_ROOT}', warn=True)
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

        print("prepare python environment...")
        download_py_packages(conn)

        #  print("migrating database....")
        #  migrate(conn)
        #  print("restarting the nginx...")
        #  restart(conn)
