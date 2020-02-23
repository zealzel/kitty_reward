from textwrap import dedent
from fabric import task
from fabcore import get_connection, Remote


@task
def nginx_trick(ctx):
    conn = get_connection(ctx)
    r = Remote(conn)
    conn.sudo('mkdir -p /etc/systemd/system/nginx.service.d')
    lines = '[Service]\nExecStartPost=/bin/sleep 0.1\n'
    r.touch(f'/etc/systemd/system/nginx.service.d/override.conf', lines, ctx.user)


@task
def restart_nginx(ctx):
    conn = get_connection(ctx)
    conn.sudo('systemctl daemon-reload')
    conn.sudo('systemctl restart nginx')


@task
def set_nginx(ctx, processname, domainname, port):
    conn = get_connection(ctx)
    r = Remote(conn)
    lines = dedent(f'''
    server {{
       listen 80;
       server_name {domainname};
       location / {{
           proxy_pass http://localhost:{port};
       }}
    }}
    ''').strip()
    r.touch(f'/etc/nginx/sites-available/{processname}', lines, ctx.user)
    conn.sudo(f'ln -s /etc/nginx/sites-available/{processname} /etc/nginx/sites-enabled/{processname}', warn=True)
    nginx_trick(ctx)
    restart_nginx(ctx)
