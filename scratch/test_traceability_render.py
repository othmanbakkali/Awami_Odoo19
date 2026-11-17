import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Test account.z.report on Company 1 for 2026-11-11
    c1 = env['res.company'].browse(1)
    z_rep = env['account.z.report'].create({
        'company_id': c1.id,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
        'report_type': 'z'
    })
    data_z = z_rep.get_report_data()
    print(f"=== Z Report on {c1.name} (2026-11-11) ===")
    print(f"Invoices count: {len(data_z['invoices'])}")
    print(f"Prior payments count: {data_z.get('prior_payments_count')}, total={data_z.get('prior_payments_total')} DH")
    
    rep_act = env['ir.actions.report'].search([('model', '=', 'account.z.report')], limit=1)
    pdf_content, _ = rep_act._render_qweb_pdf(
        rep_act.id,
        res_ids=[z_rep.id],
        data={'data': data_z}
    )
    print(f"Z Report PDF generated successfully! Action={rep_act.name}, Size={len(pdf_content)} bytes")
    with open('/tmp/test_z_traceability.pdf', 'wb') as f:
        f.write(pdf_content)
        
    # 2. Test account.sales.expense.report on Company 1 for 2026-11-11
    se_rep = env['account.sales.expense.report'].create({
        'company_id': c1.id,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
        'report_type': 'z'
    })
    data_se = se_rep.get_report_data()
    print(f"\n=== Sales & Expense Report on {c1.name} (2026-11-11) ===")
    print(f"Invoices count: {len(data_se['invoices'])}")
    print(f"Prior payments count: {data_se.get('prior_payments_count')}, total={data_se.get('prior_payments_total')} DH")
    for pp in data_se.get('prior_payments', []):
        print(f"  -> Prior Pay: {pp['payment_date']} | {pp['invoice_name']} ({pp['invoice_date']}) | {pp['partner']} | {pp['mode']} | {pp['amount']} DH")
        
    rep_act_se = env['ir.actions.report'].search([('model', '=', 'account.sales.expense.report')], limit=1)
    pdf_se, _ = rep_act_se._render_qweb_pdf(
        rep_act_se.id,
        res_ids=[se_rep.id],
        data={'data': data_se}
    )
    print(f"Sales & Expense Report PDF generated successfully! Action={rep_act_se.name}, Size={len(pdf_se)} bytes")
    with open('/tmp/test_se_traceability.pdf', 'wb') as f:
        f.write(pdf_se)
        
    # 3. Test on Company 5 (Agence Awama)
    c5 = env['res.company'].browse(5)
    se_rep_c5 = env['account.sales.expense.report'].create({
        'company_id': c5.id,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
        'report_type': 'z'
    })
    data_se_c5 = se_rep_c5.get_report_data()
    print(f"\n=== Sales & Expense Report on {c5.name} (2026-11-11) ===")
    print(f"Prior payments count: {data_se_c5.get('prior_payments_count')}, total={data_se_c5.get('prior_payments_total')} DH")
    for pp in data_se_c5.get('prior_payments', []):
        print(f"  -> Prior Pay: {pp['payment_date']} | {pp['invoice_name']} ({pp['invoice_date']}) | {pp['partner']} | {pp['mode']} | {pp['amount']} DH")
        
    pdf_c5, _ = rep_act_se._render_qweb_pdf(
        rep_act_se.id,
        res_ids=[se_rep_c5.id],
        data={'data': data_se_c5}
    )
    print(f"Company 5 PDF generated successfully! Size={len(pdf_c5)} bytes")
