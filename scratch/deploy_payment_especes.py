import os
import paramiko

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
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    
    print("2. Syncing awami_bon_magasin...")
    sftp = ssh.open_sftp()
    sync_dir(sftp, 'awami_bon_magasin', '/opt/odoo/custom-addons/awami_bon_magasin')
    sftp.close()
    
    print("3. Upgrading awami_bon_magasin...")
    cmd = (
        "systemctl stop odoo && "
        "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init' && "
        "systemctl start odoo"
    )
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("Stdout tail:")
    print('\n'.join(out.splitlines()[-15:]))
    if err:
        print("Stderr tail:")
        print('\n'.join(err.splitlines()[-15:]))
        
    ssh.close()
    print("Deployment finished!")

if __name__ == '__main__':
    main()

