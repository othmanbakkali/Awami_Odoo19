import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    wiz_cls = env['account.payment.register']
    print("default_get on wiz_cls for company 1:")
    m1448 = env['account.move'].browse(1448) # Agence Awama invoice
    defaults = wiz_cls.with_company(1).with_context(active_model='account.move', active_ids=[1]).default_get(['journal_id', 'payment_mode'])
    print("Defaults Company 1:", defaults, "journal:", env['account.journal'].browse(defaults.get('journal_id')).name if defaults.get('journal_id') else None)
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_default_journal.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_default_journal.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

