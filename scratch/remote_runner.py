import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    pfs = env['report.paperformat'].search([])
    for p in pfs:
        print(f"Paperformat: {p.id} | {p.name} | format={p.format} | dpi={p.dpi} | orientation={p.orientation} | margins=({p.margin_top},{p.margin_bottom},{p.margin_left},{p.margin_right})")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_pf.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_pf.py'")
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()
