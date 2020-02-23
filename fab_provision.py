from fabric import task
from textwrap import dedent
from fabcore import Remote


@task
def package_update(ctx):
    conn = ctx.conn
    conn.sudo('apt update')


@task
def bashrc(ctx):
    conn = ctx.conn
    r = Remote(conn)
    lines = dedent(f'''
    if [ -f ~/.bashrc ]; then
        source ~/.bashrc
    fi
    ''').strip()
    r.appends('~/.bash_profile', lines, ctx.user)


@task
def download_pip(ctx):
    ''' === underscore is replaced with hyphens ===
        fab download-pip
    '''
    url = 'https://bootstrap.pypa.io/get-pip.py'
    conn = ctx.conn
    conn.run(f'curl {url} -o get-pip.py')
    '''
        copy pip binary into ~/.local/bin
    '''
    conn.run('python3 get-pip.py')


@task
def install_pip(ctx):
    conn = ctx.conn
    conn.sudo('apt install -y python3-pip')


@task
def pyenv(ctx, filerc, python_ver, virtualenv_name):
    conn = ctx.conn
    r = Remote(conn)
    '''
    Prerequisites for ubuntu
    reference: https://github.com/pyenv/pyenv/wiki/Common-build-problems
    '''
    conn.sudo('apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
              libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
              xz-utils tk-dev libffi-dev liblzma-dev python-openssl git')

    home = conn.run('echo $HOME').stdout.strip()
    path = conn.run('echo $PATH').stdout.strip()
    pyenv_root = f'{home}/.pyenv'

    with conn.cd(home):
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
            r.appends(filerc, content, ctx.user)

        print('pyenv installed. download pyenv-virtualenv')
        '''
        pyenv-virtualenv respository at github
        https://github.com/pyenv/pyenv-virtualenv
        '''
        conn.run('git clone https://github.com/pyenv/pyenv-virtualenv.git'
                 f' {pyenv_root}/plugins/pyenv-virtualenv', warn=True)
        conn.run(
            f'source {filerc};'
            f'pyenv install {python_ver};'
            f'pyenv virtualenv {python_ver} {virtualenv_name}'
        )
