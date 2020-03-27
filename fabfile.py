import os
import re
import sys
from textwrap import dedent
from fabric import Connection, task

# fabcore is my own package located in ~/bin
home =os.path.expanduser('~')
sys.path.insert(0, f'{home}/bin')
from fabcore.fab_core import Remote, get_connection
from fabcore.fab_nginx import setup_nginx
from fabcore.fab_provision import package_update, download_pip, pyenv, install_pip
from fabcore.fab_git import pull, clone
from fabcore.fab_deploy import (
    download_py_packages, gunicorn_service_systemd, start_service, install_certbot
)

PROJECT_NAME = 'kitty_reward'
HOME = '~'
PROJECT_ROOT = f'{HOME}/codes'
PROJECT_PATH = f'{PROJECT_ROOT}/{PROJECT_NAME}'
FILE_RC = f'{HOME}/.bash_profile'

REPO_URL = f'https://github.com/zealzel/{PROJECT_NAME}.git'
LOCAL_USER = 'zealzel'

#  MY_DOMAIN_COM = 'momomuji.xyz'
MY_DOMAIN_COM = 'zealzel.xyz'
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
def tmp(ctx):
    conn = ctx.conn
    print('ctx.config.run.env', ctx.config.run.env)
    conn.run('echo $BASH_ENV')
    conn.run('pyenv --version')


@task
def install_apache2(ctx):
    conn = ctx.conn
    conn.sudo('systemctl stop apache2', warn=True)
    conn.sudo('apt install -y apache2')


@task
def setup_apache2(ctx, projname, mydomain, port=80):
    conn = ctx.conn
    r = Remote(conn)
    home = f'/home/zealzel/codes/{projname}'
    #  lines = dedent(f'''
    #  <VirtualHost *:{port}>
        #  ServerName {mydomain}
        #  ServerAdmin {ctx.user}@localhost
        #  DocumentRoot /var/www/wordpress_{projname}
        #  <Directory /var/www/wordpress_{projname}/>
            #  AllowOverride All
        #  </Directory>
        #  ErrorLog ${{APACHE_LOG_DIR}}/error.log
        #  CustomLog ${{APACHE_LOG_DIR}}/access.log combined
    #  </VirtualHost>
    #  ''').strip()
    lines = dedent(f'''
    <VirtualHost *:80>
        ServerName {mydomain}
        ServerAdmin {ctx.user}@localhost
        DocumentRoot {home}
        <Directory {home}/>
            AllowOverride All
        </Directory>
        ErrorLog ${{APACHE_LOG_DIR}}/error.log
        CustomLog ${{APACHE_LOG_DIR}}/access.log combined
        ProxyRequests off
        ProxyPass / http://127.0.0.1:{port}
        ProxyPassReverse / http://127.0.0.1:{port}
    </VirtualHost>
    ''').strip()
    r.touch(f'/etc/apache2/sites-available/{projname}.conf', lines, ctx.user)

    # change /etc/apache2/port.conf  --> TBD
    #  out = r.fetch_txt(f'/etc/apache2/ports.conf').split('\n')
    #  listens = []
    #  for i, line in enumerate(out):
        #  matched = re.search('^Listen\s+(\d{2,5})$', line)
        #  if matched:
            #  listens.append([i, int(matched.groups()[0])])
    #  if port not in [e[1] for e in listens]:
        #  out.insert(listens[-1][0]+1, f'Listen {port}')
    #  if listens[0][1]==80:
        #  del out[listens[0][0]]
    #  with open('ports.conf.tmp', 'w') as f:
        #  f.write('\n'.join(out))
    #  conn.put('ports.conf.tmp')
    #  conn.sudo('mv ports.conf.tmp /etc/apache2/ports.conf')

    conn.sudo('a2enmod rewrite', warn=True)
    conn.sudo('a2enmod proxy', warn=True)
    conn.sudo('a2enmod proxy_http', warn=True)
    conn.sudo(f'ln -s /etc/apache2/sites-available/{projname}.conf '
              f'/etc/apache2/sites-enabled/{projname}.conf', warn=True)
    conn.sudo(f'rm /etc/apache2/sites-enabled/000-default.conf', warn=True)
    conn.sudo('systemctl restart apache2')


@task
def prepare(ctx):
    conn = ctx.conn
    conn.sudo('systemctl stop apache2', warn=True)
    conn.sudo('systemctl stop nginx', warn=True)


@task
def provision(ctx):
    print('\n\npackage_update')
    package_update(ctx)
    print('\n\nprepare')
    prepare(ctx)
    print('\n\ninstall pip')
    install_pip(ctx)
    print('\n\npyenv prepare')
    pyenv(ctx, FILE_RC, PYTHON_VER, VIRTUALENV_NAME)
    print('\n\ninstall apache2')
    install_apache2(ctx)


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

    print("\n\nrestarting the systemd...")
    gunicorn_service_systemd(ctx, SERVICENAME, PROJECT_NAME, APPNAME, VIRTUALENV_NAME, PORT)


    print("\n\nsetup apache2...")
    setup_apache2(ctx, PROJECT_NAME, MY_DOMAIN_COM, PORT)

    #  # install nginx
    #  r.apt_install('nginx')

    #  print("\n\nsetup the nginx...")
    #  setup_nginx(ctx, PROJECT_NAME, MY_DOMAIN_COM, PORT)

    #install certbot
    print("\n\ninstall certbot...")
    install_certbot(ctx)
