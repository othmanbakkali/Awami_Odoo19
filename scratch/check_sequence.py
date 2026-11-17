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
    m1800 = env['account.move'].browse(1800)
    journal = m1800.journal_id
    print("Journal:", journal.name, "id:", journal.id)
    print("Journal sequence fields:", [f for f in journal._fields if 'seq' in f])
    
    # Check ir.sequence
    seqs = env['ir.sequence'].search(['|', ('name', 'ilike', 'BL'), ('code', 'ilike', 'account.move')])
    for s in seqs:
        print(f"Sequence: {s.name} code={s.code} prefix={s.prefix} number_next={s.number_next}")
        
    # Check sequence.mixin fields on account.move
    print("sequence.mixin fields on move:", [f for f in m1800._fields if 'sequence' in f or 'highest' in f or 'name' in f])
    if hasattr(m1800, 'sequence_prefix'):
        print("m1800.sequence_prefix:", m1800.sequence_prefix)
        print("m1800.sequence_number:", m1800.sequence_number)
        
    # Check what the highest name is for 2026/11/11
    today_moves = env['account.move'].search([('journal_id', '=', journal.id), ('name', 'ilike', 'BL/2026/11/11/')], order='name desc', limit=5)
    print("\nLatest moves for 2026/11/11:")
    for tm in today_moves:
        print(f"  {tm.name} (id={tm.id}, state={tm.state})")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_seq.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_seq.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

