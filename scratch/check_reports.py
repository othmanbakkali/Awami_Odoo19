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
    reps = env['ir.actions.report'].search([('model', '=', 'account.move')])
    for r in reps:
        pf_name = r.paperformat_id.name if r.paperformat_id else 'None'
        pf_fmt = f"{r.paperformat_id.format}, {r.paperformat_id.orientation}" if r.paperformat_id else ''
        print(f"Report: id={r.id} | name={r.name} | xml_id={r.xml_id} | report_name={r.report_name} | pf={pf_name} ({pf_fmt})")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/list_move_reports.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/list_move_reports.py'")
    print(stdout.read().decode())
    ssh.close()

