import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    comps = env['res.company'].search([])
    for c in comps:
        journals = env['account.journal'].search([('company_id', '=', c.id)])
        print(f"Company: {c.id} - {c.name}")
        for j in journals:
            print(f"   Journal: id={j.id}, code={j.code}, name={j.name}, type={j.type}, active={j.active}")

