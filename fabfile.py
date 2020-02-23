from textwrap import dedent
from fabric import Connection, task
from fabcore import Remote, get_connection
from fab_nginx import set_nginx
from fab_provision import package_update, download_pip, pyenv
from fab_git import pull, clone
from fab_deploy import download_py_packages, gunicorn_service_systemd, start_service


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
SERVICENAME = PROJECT_NAME


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
def deploy(ctx):
    conn = ctx.conn
    r = Remote(conn)
    clone(ctx, REPO_URL, PROJECT_ROOT, PROJECT_NAME)
    with conn.cd(PROJECT_PATH):
        #  print("checkout to dev branch...")
        #  checkout(conn, branch="dev")

        print("pulling latest code from dev branch...")
        pull(ctx, PROJECT_PATH)

        print("prepare python environment...")
        download_py_packages(ctx, PROJECT_PATH, FILE_RC, VIRTUALENV_NAME)

    #  print("migrating database....")
    #  migrate(conn)

    print("restarting the systemd...")
    gunicorn_service_systemd(ctx, SERVICENAME, PROJECT_NAME, APPNAME, VIRTUALENV_NAME, PORT)

    # install nginx
    r.apt_install('nginx')

    print("setup the nginx...")
    set_nginx(ctx, PROJECT_NAME, MY_DOMAIN_COM, PORT)
