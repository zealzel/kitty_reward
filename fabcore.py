from textwrap import dedent
from fabric import Connection, task


def defined_kwargs(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


def get_connection(ctx):
    return Connection(
    **defined_kwargs(
        host=ctx.host,
        user=ctx.user,
        port=ctx.port,
        connect_kwargs={"key_filename": ctx.key},
        inline_ssh_env=True,
        forward_agent=ctx.forward_agent)
    )


class Remote():
    def __init__(self, c):
        self.c = c

    def remote_var(self, varname):
        return self.c.run(f'echo ${varname}', hide=True).stdout.strip()

    @property
    def home(self):
        return self.remote_var('HOME')

    def touch(self, file, lines, user):
        self.c.run(
            f'sudo touch {file};'
            f'sudo chown {user}:{user} {file};'
            f"echo -e '{lines}' > {file}"
            )

    def appends(self, file, lines, user):
        lines_already_there = False
        if self.file_exist(file):
            content = self.fetch_txt(file)
            lines_already_there = lines in content
        if not lines_already_there:
            self.c.run(
                f'sudo touch {file};'
                f'sudo chown {user}:{user} {file};'
                f"echo -e '{lines}' >> {file}"
            )

    def apt_install(self, package):
        self.c.sudo(f'apt install -y {package}')

    def fetch_txt(self, filepath):
        return self.c.run(f'cat {filepath}', hide=True).stdout

    def file_exist(self, filepath):
        out = self.c.run(f'[ -f {filepath} ] && echo 1', warn=True, hide=True).stdout
        return True if out else False

    def ls(self):
        return self.c.run('ls -al')


@task
def appends_test(ctx):
    conn = get_connection(ctx)
    r = Remote(conn)
    file = '~/.bash_profile'

    # test1: single line
    content1 = 'export PATH=$HOME/.local/bin:$PATH'

    # test2: multiple lines
    content2 = dedent('''
    if command -v pyenv 1>/dev/null 2>&1; then
      eval "$(pyenv init -)"
    fi
    ''').strip()

    r.appends(file, content1, ctx.user)
    r.appends(file, content2, ctx.user)
    

