import sys
import os
import paramiko

def run_remote_script(local_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    
    sftp = ssh.open_sftp()
    remote_path = '/tmp/' + os.path.basename(local_path)
    sftp.put(local_path, remote_path)
    sftp.close()
    
    cmd = f"su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 {remote_path}'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("STDERR:", err, file=sys.stderr)
    ssh.close()

if __name__ == '__main__':
    run_remote_script(sys.argv[1])

