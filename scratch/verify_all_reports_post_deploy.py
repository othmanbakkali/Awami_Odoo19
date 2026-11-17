import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

verify_script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Verification Z-Report pour le 11/11/2026
    z = env['account.z.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    if z:
        z.generate_snapshot_data()
        d = z.get_report_data()
        print("=== Z-REPORT 11/11/2026 ===")
        print("Summary total_total:", d['summary']['total_total'])
        print("Summary invoices_paid:", d['summary']['invoices_paid'])
        print("Summary total_residual:", d['summary']['total_residual'])
        print("Prior payments total:", d.get('prior_payments_total'))
        print("Summary total_paid (payments_total):", d['summary']['total_paid'])
        print("Payments table lines:")
        p_sum = 0
        for p in d['payments']:
            print(f"  Mode: {p['mode']} | Nb: {p['count']} | Amount: {p['amount']}")
            p_sum += p['amount']
        print("Sum of payments table lines:", p_sum)
        
        # Render PDF
        report_action = env.ref('etat_vente_journalier_facture.action_report_z', False) or env.ref('Etat_Vente_Journalier_facturé.action_report_z')
        pdf_bytes, _ = report_action._render_qweb_pdf(report_action.id, [z.id])
        with open('/tmp/z_11_11_verified.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print(f"Rendered Z-Report PDF: {len(pdf_bytes)} bytes")
        
    # 2. Verification Z-Report pour le 02/11/2026
    z2 = env['account.z.report'].search([('date_start', '=', '2026-11-02'), ('date_end', '=', '2026-11-02')], limit=1)
    if z2:
        z2.generate_snapshot_data()
        d2 = z2.get_report_data()
        print("=== Z-REPORT 02/11/2026 ===")
        print(f"Cheques count: {len(d2.get('cheques', []))}")
        for c in d2.get('cheques', []):
            print(f"  Cheque: {c.get('check_number')} | Client: {c.get('partner')} | Tireur: {c.get('check_client_name')} | Amount: {c.get('amount')} | Inv: {c.get('invoice_name')}")
            
    # 3. Verification Sales & Expense Report 11/11/2026
    se = env['account.sales.expense.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    if se:
        se.generate_snapshot_data()
        dse = se.get_report_data()
        print("=== SALES & EXPENSE REPORT 11/11/2026 ===")
        print("Sales Net:", dse['summary']['sales_net'])
        print("Total Expenses:", dse['summary']['total_expenses_global'])
        print("Net Result:", dse['summary']['net_result'])
        print("Net Cashbox:", dse['summary']['net_cashbox'])
        report_action_se = env.ref('Report.action_report_sales_expense', False)
        if report_action_se:
            pdf_se, _ = report_action_se._render_qweb_pdf(report_action_se.id, [se.id])
            with open('/tmp/se_11_11_verified.pdf', 'wb') as f:
                f.write(pdf_se)
            print(f"Rendered SE Report PDF: {len(pdf_se)} bytes")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_reports.py', 'w') as f:
    f.write(verify_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/verify_reports.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())

sftp = ssh.open_sftp()
try:
    sftp.get('/tmp/z_11_11_verified.pdf', r'c:\Projects\Awami OUssama\scratch\z_11_11_verified.pdf')
    print("Downloaded z_11_11_verified.pdf")
except Exception as e:
    print("Could not download z_11_11_verified.pdf:", e)

try:
    sftp.get('/tmp/se_11_11_verified.pdf', r'c:\Projects\Awami OUssama\scratch\se_11_11_verified.pdf')
    print("Downloaded se_11_11_verified.pdf")
except Exception as e:
    print("Could not download se_11_11_verified.pdf:", e)

sftp.close()
ssh.close()
