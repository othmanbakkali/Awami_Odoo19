import os
import sys
import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

def sync_dir(sftp, local_dir, remote_dir):
    try:
        sftp.mkdir(remote_dir)
    except Exception:
        pass
    for item in os.listdir(local_dir):
        l_path = os.path.join(local_dir, item)
        r_path = os.path.join(remote_dir, item).replace('\\', '/')
        if os.path.isdir(l_path):
            sync_dir(sftp, l_path, r_path)
        else:
            sftp.put(l_path, r_path)

def main():
    print("1. Connecting to remote server...")
    ssh = get_ssh()
    sftp = ssh.open_sftp()
    
    print("2. Syncing files...")
    # Sync Etat_Vente_Journalier_facturé
    evj_local = "Etat_Vente_Journalier_facturé"
    for r_dest in ["/opt/odoo/custom-addons/etat_vente_journalier_facture", "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé"]:
        print(f"  Syncing {evj_local} -> {r_dest}")
        sync_dir(sftp, evj_local, r_dest)
        
    # Sync Report
    rep_local = "Report"
    rep_remote = "/opt/odoo/custom-addons/Report"
    print(f"  Syncing {rep_local} -> {rep_remote}")
    sync_dir(sftp, rep_local, rep_remote)
    
    # Sync awami_bon_magasin
    abm_local = "awami_bon_magasin"
    abm_remote = "/opt/odoo/custom-addons/awami_bon_magasin"
    print(f"  Syncing {abm_local} -> {abm_remote}")
    sync_dir(sftp, abm_local, abm_remote)
    
    sftp.close()
    
    print("3. Upgrading modules safely...")
    # Stop odoo, upgrade, restart
    upgrade_cmd = (
        "systemctl stop odoo && "
        "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u etat_vente_journalier_facture,Report,awami_bon_magasin --stop-after-init' && "
        "systemctl start odoo"
    )
    stdin, stdout, stderr = ssh.exec_command(upgrade_cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("Upgrade stdout tail:")
    print('\n'.join(out.splitlines()[-20:]))
    if err:
        print("Upgrade stderr tail:")
        print('\n'.join(err.splitlines()[-20:]))
        
    ssh.close()
    print("Done deploying!")

if __name__ == '__main__':
    main()

