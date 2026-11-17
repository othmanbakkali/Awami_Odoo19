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
    
    print("account.account fields with company:", [f for f in env['account.account']._fields if 'comp' in f])
    
    # Check journal 6, 52, 53, 9 in company 1
    for jid in [6, 52, 53, 9]:
        j = env['account.journal'].browse(jid)
        print(f"Journal {j.id}: name='{j.name}' code='{j.code}' type='{j.type}'")
        print(f"  default_account_id: {j.default_account_id.id} code={j.default_account_id.code} name='{j.default_account_id.name}'")
        print(f"  suspense_account_id: {j.suspense_account_id.id if getattr(j, 'suspense_account_id', False) else None}")
        print(f"  payment_method_lines (inbound):")
        for m in j.inbound_payment_method_line_ids:
            print(f"    id={m.id} name='{m.name}' method_code={m.payment_method_id.code} payment_account_id={m.payment_account_id.id if m.payment_account_id else None}")
        print(f"  payment_method_lines (outbound):")
        for m in j.outbound_payment_method_line_ids:
            print(f"    id={m.id} name='{m.name}' method_code={m.payment_method_id.code} payment_account_id={m.payment_account_id.id if m.payment_account_id else None}")

    # Check journal Bank in other companies (e.g. jid=36 for Agence Awama)
    j_awama = env['account.journal'].browse(36)
    print("\nAgence Awama Bank journal (id=36):")
    print(f"  default_account_id: {j_awama.default_account_id.id if j_awama.default_account_id else None}")
    print(f"  suspense_account_id: {j_awama.suspense_account_id.id if getattr(j_awama, 'suspense_account_id', False) else None}")
    for m in j_awama.inbound_payment_method_line_ids:
        print(f"    inbound id={m.id} name='{m.name}' method_code={m.payment_method_id.code} payment_account_id={m.payment_account_id.id if m.payment_account_id else None}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_journal_details.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_journal_details.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

