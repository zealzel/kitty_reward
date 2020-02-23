from textwrap import dedent
from fabric import task
from fabcore import get_connection, Remote

@task
def download_py_packages(ctx, project_path, file_rc, virtualenv_name):
    conn= get_connection(ctx)
    with conn.cd(project_path):
        conn.run(
            f'source {file_rc} &&'
            f'pyenv activate {virtualenv_name} &&'
            f'pip install -U pip &&'
            f'pip install -r requirements.txt'
        )


@task
def gunicorn_service_systemd(ctx, servicename, project_name, appname, virtualenv_name, port):
    conn = ctx.conn
    r = Remote(conn)
    pyenv_root = f'{r.home}/.pyenv'
    project_path = f'{r.home}/codes/{project_name}'
    lines = dedent(f'''
    [Unit]
    Description=Gunicorn instance to serve {appname}
    After=network.target

    [Service]
    User={ctx.user}
    Group=www-data
    WorkingDirectory={project_path}
    Environment=PATH={pyenv_root}/versions/{virtualenv_name}/bin:$PATH
    ExecStart={pyenv_root}/versions/{virtualenv_name}/bin/gunicorn --workers 3 --bind 0.0.0.0:{port} app:app
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
