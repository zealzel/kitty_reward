from fabric import task

@task
def pull(ctx, project_path, branch="master"):
    conn = ctx.conn
    with conn.cd(project_path):
        conn.run(f'git pull origin {branch}')


@task
def clone(ctx, repo_url, project_root, project_name):
    conn = ctx.conn
    conn.run(f'mkdir -p {project_root}', warn=True)
    with conn.cd(project_root):
        ls_result = conn.run("ls").stdout
        ls_result = ls_result.split("\n")
        if project_name in ls_result:
            print("project already exists")
            return
        conn.run(f'git clone {repo_url} {project_name}')
