from textwrap import dedent
from fabric import Connection, task
from fabcore import Remote, get_connection, appends_test
from fab_nginx import set_nginx
from provision import package_update, download_pip, pyenv

PROJECT_NAME = 'kitty_reward'
HOME = '~'
PROJECT_ROOT = f'{HOME}/codes'
PROJECT_PATH = f'{PROJECT_ROOT}/{PROJECT_NAME}'
FILE_RC = f'{HOME}/.bash_profile'

REPO_URL = f'https://github.com/zealzel/{PROJECT_NAME}.git'
LOCAL_USER = 'zealzel'

#  MY_DOMAIN_COM = 'momomuji.xyz'
MY_DOMAIN_COM = 'fitfabsw.club'
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
    conn = get_connection(ctx)
    ctx.conn = conn


@task
def linode(ctx):
    ctx.user = 'zealzel'
    ctx.vagrant_box = None
    ctx.host = '172.104.182.76'
    ctx.port = None
    ctx.key = None
    #  ctx.key = f'/Users/{LOCAL_USER}/.ssh/id_rsa'
    #  ctx.forward_agent = False
    conn = get_connection(ctx)
    ctx.conn = conn


@task
def provision(ctx):
    package_update(ctx)
    download_pip(ctx)
    pyenv(ctx, FILE_RC, PYTHON_VER, VIRTUALENV_NAME)


@task
def download_py_packages(ctx):
    conn= get_connection(ctx)
    with conn.cd(PROJECT_PATH):
        conn.run(
            f'source {FILE_RC} &&'
            f'pyenv activate {VIRTUALENV_NAME} &&'
            f'pip install -U pip &&'
            f'pip install -r requirements.txt'
        )


@task
def echo(ctx, message): # with arguments
    ''' === with positional argument ===
        fab echo --message some_message
    '''
    conn = get_connection(ctx)
    conn.run(f'echo {message}')


@task
def pull(ctx, branch="master"):
    conn = ctx.conn
    with conn.cd(PROJECT_PATH):
        conn.run(f'git pull origin {branch}')


@task
def clone(ctx):
    conn = ctx.conn
    conn.run(f'mkdir -p {PROJECT_ROOT}', warn=True)
    with conn.cd(PROJECT_ROOT):
        ls_result = conn.run("ls").stdout
        ls_result = ls_result.split("\n")
        if PROJECT_NAME in ls_result:
            print("project already exists")
            return
        conn.run(f'git clone {REPO_URL} {PROJECT_NAME}')


@task
def deploy(ctx):
    conn = ctx.conn
    r = Remote(conn)
    clone(ctx)
    with conn.cd(PROJECT_PATH):
        #  print("checkout to dev branch...")
        #  checkout(conn, branch="dev")

        print("pulling latest code from dev branch...")
        pull(ctx)

        print("prepare python environment...")
        download_py_packages(ctx)

    #  print("migrating database....")
    #  migrate(conn)

    print("restarting the systemd...")
    gunicorn_service_systemd(ctx, SERVICE_NAME)

    # install nginx
    r.apt_install('nginx')

    print("setup the nginx...")
    set_nginx(ctx, PROJECT_NAME, MY_DOMAIN_COM, PORT)


@task
def gunicorn_service_systemd(ctx, servicename):
    conn = ctx.conn
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
    start_service(ctx, servicename)


@task
def start_service(ctx, servicename):
    conn = ctx.conn
    conn.sudo(f'systemctl daemon-reload')
    conn.sudo(f'systemctl restart {servicename}')
