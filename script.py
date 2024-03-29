from tabulate import tabulate
from colorama import Fore, Style
import getpass
import paramiko
import sys
import select

# ------------- Config The Script ------------- #

host_list = ['192.168.1.137', 'localhost'] # Hosts to which to collect information
port = 22 # The ssh port, depending on the port you use, usually 22.
username = 'rompelhd' # Change it for your user, you can create one to use for this purpose. "It can be that some data collection may fail due to lack of permissions for example the packages".
password = '' # You can specify a password to facilitate the automated use of the script, it is not secure at the moment because it is in plain text.

# --------------------------------------------- #

if password == "":
    password = getpass.getpass("Introduce tu contraseña: ")

table_data = []
cpu_usage = []
mem_usage = []
pack_ins = []

def ssh_client_remote(stdin, stdout, shell):
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = input()
            if command.lower() == 'exit':
                break
            stdin.write(command + '\n')
            stdin.flush()

        if shell.recv_ready():
            output = shell.recv(1024).decode()
            if output:
                print(output, end='')

for host in host_list:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=host, username=username, password=password)

        shell = client.invoke_shell()
        stdin = shell.makefile('wb')
        stdout = shell.makefile('r')

        if "--al" in sys.argv:
            stdin, stdout, stderr = client.exec_command("python3 /home/rompelhd/ServerConnect/main.py")
        elif "--shell" in sys.argv or "-s" in sys.argv:
            ssh_client_remote(stdin, stdout, shell)
        elif len(sys.argv) == 1:
            stdin, stdout, stderr = client.exec_command("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\\1/'")
            cpu_usage.append(stdout.read().decode().strip())

            stdin, stdout, stderr = client.exec_command("free | grep Mem | awk '{print $3/$2 * 100.0}'")
            mem_usage.append(stdout.read().decode().strip())

            stdin, stdout, stderr = client.exec_command("expr $(dpkg-query -l | wc -l) - 5")
            pack_ins.append(stdout.read().decode().strip())

    except paramiko.AuthenticationException:
        print(f"No se pudo autenticar en {host}")
    except paramiko.SSHException as sshException:
        print(f"Error de conexión SSH en {host}: {sshException}")
    finally:
        if client:
            client.close()
            shell.close()
            del client, stdin, stdout, stderr

for i in range(len(cpu_usage)):
    if i < len(mem_usage) and i < len(pack_ins):
        table_data.append([host_list[i], cpu_usage[i], mem_usage[i], pack_ins[i]])

headers = [Fore.RED + "Server IP" + Style.RESET_ALL, Fore.RED + "CPU Usage" + Style.RESET_ALL, Fore.RED + "Ram Usage" + Style.RESET_ALL, Fore.RED + "Packages" + Style.RESET_ALL]

if table_data:
    print(tabulate(table_data, headers, tablefmt="fancy_grid"))
else:
    pass
