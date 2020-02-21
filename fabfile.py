from textwrap import dedent
from fabric import Connection, task
from fabcore import Remote, get_connection, appends_test

PROJECT_NAME = 'kitty_reward'
HOME = '~'
PROJECT_ROOT = f'{HOME}/codes'
PROJECT_PATH = f'{PROJECT_ROOT}/{PROJECT_NAME}'
FILE_RC = f'{HOME}/.bash_profile'

REPO_URL = f'https://github.com/zealzel/{PROJECT_NAME}.git'
LOCAL_USER = 'zealzel'

PORT = 5223


PYTHON_VER = '3.7.0'
VIRTUALENV_NAME = PROJECT_NAME
APPNAME = PROJECT_NAME
SERVICE_NAME = PROJECT_NAME


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


@task
def provision(ctx):
    with get_connection(ctx) as conn:
        package_update(conn)
        download_pip(conn)
        pyenv(conn)


@task
def package_update(ctx):
    conn = get_connection(ctx)
    conn.run('sudo apt update')



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
            appends(conn, FILE_RC, ctx.user, content)

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
        conn.run(f'git pull origin {branch}')


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
        conn.run(f'git clone {REPO_URL} {PROJECT_NAME}')


@task
def deploy(ctx):
    conn = get_connection(ctx)
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

        print("restarting the systemd...")
        gunicorn_service_systemd(conn, SERVICE_NAME)

        #  print("restarting the nginx...")
        #  restart(conn)


@task
def gunicorn_service_systemd(ctx, servicename):
    conn = get_connection(ctx)
    r = Remote(conn)
    pyenv_root = f'{r.home}/.pyenv'
    project_path = f'{r.home}/codes/{PROJECT_NAME}'
    lines = dedent(f'''
    [Unit]
    Description=Gunicorn instance to serve {APPNAME}
    After=network.target

    [Service]
    User={ctx.user}
    Group=www-data
    WorkingDirectory={project_path}
    Environment=PATH={pyenv_root}/versions/{VIRTUALENV_NAME}/bin:$PATH
    ExecStart={pyenv_root}/versions/{VIRTUALENV_NAME}/bin/gunicorn --workers 3 --bind 0.0.0.0:{PORT} app:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ''').strip()
    r.touch(f'/etc/systemd/system/{servicename}.service', lines, ctx.user)
    start_service(conn, servicename)


@task
def start_service(ctx, servicename):
    conn = get_connection(ctx)
    conn.sudo('systemctl daemon-reload')
    conn.sudo(f'systemctl restart {servicename}')
