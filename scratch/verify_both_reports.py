import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID, fields
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    for model_name in ['account.z.report', 'account.sales.expense.report']:
        print(f"\\n=======================================================")
        print(f"               TESTING {model_name}")
        print(f"=======================================================")
        
        # Test 1: 11/11/2026
        rep11 = env[model_name].create({
            'company_id': 1,
            'date_start': '2026-11-11',
            'date_end': '2026-11-11',
        })
        d11 = rep11.get_report_data()
        print(f"--- {model_name} on 11/11/2026 ---")
        print(f"Invoices count: {len(d11['invoices'])}")
        for inv in d11['invoices']:
            if 'Slawi' in inv['partner'] or '0006' in inv['name'] or '0021' in inv['name']:
                print(f"  Slawi inv: name={inv['name']}, total={inv['total']}, paid={inv['paid']}, residual={inv['residual']}, state={inv['payment_state']}, mode={inv['payment_mode']}")
        print(f"Cheques table count: {len(d11.get('cheques', []))}")
        for c in d11.get('cheques', []):
            print(f"  Cheque: {c}")
        if 'payments' in d11:
            for p in d11['payments']:
                print(f"  Payment mode: {p['mode']}, amount: {p['amount']}, count: {p['count']}")
                if p['mode'] in ('Chèque', 'Effet'):
                    for dt in p.get('details', []):
                        print(f"     -> {dt}")
                        
        # Test 2: 02/11/2026
        rep02 = env[model_name].create({
            'company_id': 1,
            'date_start': '2026-11-02',
            'date_end': '2026-11-02',
        })
        d02 = rep02.get_report_data()
        print(f"\\n--- {model_name} on 02/11/2026 ---")
        print(f"Cheques table count: {len(d02.get('cheques', []))}")
        for c in d02.get('cheques', []):
            print(f"  Cheque: date={c['date']}, inv={c['invoice_name']}, client={c.get('check_client_name') or c.get('partner')}, num={c['check_number']}, amt={c['amount']}, state={c.get('state') or c.get('payment_state')}")
"""

with sftp.file('/tmp/verify_both_reports.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/verify_both_reports.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

