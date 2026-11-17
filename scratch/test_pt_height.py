import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    test_template = """
    <!-- Template Principal : 2 Bons A5 sur la Même Page A4 (Centrage Parfait à 148.5mm) -->
    <template id="report_invoice_a5_template">
        <t t-call="web.html_container">
            <meta charset="utf-8"/>
            <t t-foreach="docs" t-as="o">
                <div class="page" t-att-style="'font-family: DejaVu Sans, Arial, sans-serif; width: 100%; box-sizing: border-box; padding: 0; margin: 0; page-break-inside: avoid;' + (' page-break-after: always;' if not o_last else ' page-break-after: avoid;')">
                    <meta charset="utf-8"/>
                    <!-- 1. PREMIER EXEMPLAIRE (HAUT DE PAGE : 0 à 148.5mm) : COPIE CLIENT -->
                    <div style="height: 395pt; box-sizing: border-box; overflow: hidden;">
                        <t t-set="copy_label" t-value="'(COPIE CLIENT)'"/>
                        <t t-call="awami_bon_magasin.report_invoice_a5_single_bon"/>
                    </div>

                    <!-- LIGNE DE DÉCOUPE / SÉPARATION EXACTE AU MILIEU DE PAGE A4 (y = 421pt = 148.5mm) -->
                    <div style="height: 12pt; line-height: 12pt; text-align: center; margin: 0; border-top: 1px dashed #94a3b8; box-sizing: border-box; position: relative;">
                        <span style="position: absolute; top: -6pt; left: 50%; transform: translateX(-50%); background: #ffffff; padding: 0 8px; font-size: 7.5pt; color: #64748b; font-weight: bold; letter-spacing: 1px;">
                            - - - - - - - - - - - - - - - - - DÉCOUPE MILIEU DE PAGE A4 - - - - - - - - - - - - - - - - -
                        </span>
                    </div>

                    <!-- 2. DEUXIÈME EXEMPLAIRE (BAS DE PAGE : 148.5mm à 297mm) : COPIE CONTRÔLE -->
                    <div style="height: 395pt; box-sizing: border-box; overflow: hidden;">
                        <t t-set="copy_label" t-value="'(COPIE CONTRÔLE)'"/>
                        <t t-call="awami_bon_magasin.report_invoice_a5_single_bon"/>
                    </div>
                </div>
            </t>
        </t>
    </template>
"""
    # Replace in local report_invoice_a5.xml
    with open('awami_bon_magasin/report/report_invoice_a5.xml', 'r', encoding='utf-8') as f:
        full_xml = f.read()
    
    # Extract before and after report_invoice_a5_template
    start_tag = '<!-- Template Principal : 2 Bons A5 sur la Même Page A4'
    end_tag = '<!-- Template Principal : 1 Seul Bon sur Page Format A5 -->'
    
    p1 = full_xml[:full_xml.find(start_tag)]
    p2 = full_xml[full_xml.find(end_tag):]
    
    new_xml = p1 + test_template + '    ' + p2
    with open('awami_bon_magasin/report/report_invoice_a5.xml', 'w', encoding='utf-8') as f:
        f.write(new_xml)
        
    sftp = ssh.open_sftp()
    with sftp.file('/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml', 'w') as f:
        f.write(new_xml)
    sftp.close()

    cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    stdout.read()

    # Render verify_2on1_pt.pdf
    render_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    inv = env['account.move'].browse(1448)
    report = env.ref('awami_bon_magasin.action_report_invoice_a5')
    pdf, _ = report._render_qweb_pdf(report.id, [inv.id])
    with open('/tmp/verify_2on1_pt.pdf', 'wb') as f:
        f.write(pdf)
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/render_pt.py', 'w') as f:
        f.write(render_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_pt.py'")
    print(stdout.read().decode())

    sftp = ssh.open_sftp()
    sftp.get('/tmp/verify_2on1_pt.pdf', 'scratch/verify_2on1_pt.pdf')
    sftp.close()
    print("Downloaded scratch/verify_2on1_pt.pdf")
    ssh.close()

