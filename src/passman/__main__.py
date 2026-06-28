import argparse
import getpass

import cmd
from typing import IO

from passman.auth import signup, login

from passman.crypto import derive_key

from passman.database import fetchall

from passman.schema import init_db

import passman.vault as vault


class PassManShell(cmd.Cmd):
    ASCII_ART = """
██████╗  █████╗ ███████╗███████╗███╗   ███╗ █████╗ ███╗   ██╗
██╔══██╗██╔══██╗██╔════╝██╔════╝████╗ ████║██╔══██╗████╗  ██║
██████╔╝███████║███████╗███████╗██╔████╔██║███████║██╔██╗ ██║
██╔═══╝ ██╔══██║╚════██║╚════██║██║╚██╔╝██║██╔══██║██║╚██╗██║
██║     ██║  ██║███████║███████║██║ ╚═╝ ██║██║  ██║██║ ╚████║
╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
                                                                            
"""
    intro: str = (
        ASCII_ART + "\nPassMan: keep your passwords local, encrypted, and yours."
    )
    prompt: str = "(passman) "

    username: str
    key: bytes

    def __init__(
        self,
        username: str,
        key: bytes,
        completekey: str = "tab",
        stdin: IO[str] | None = None,
        stdout: IO[str] | None = None,
    ) -> None:
        super().__init__(completekey, stdin, stdout)
        self.username: str = username
        self.key: bytes = key

    def preloop(self) -> None:
        print("Commands:")
        print("  (a)dd <name>")
        print("  (g)et <name>")
        print("  (u)pdate <name>")
        print("  (d)elete <name>")
        print("  (e)xit / (b)ye")

    def do_help(self, arg: str) -> bool | None:
        return super().do_help(arg)

    def do_bye(self, arg: str) -> bool:
        print("Exiting...")
        return True

    def do_add(self, arg: str):
        name = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        plaintext_password: str = getpass.getpass("Password: ")
        if not plaintext_password:
            print("Password cannot be empty")
            return
        vault.create(
            username=self.username,
            name=name,
            plaintext_password=plaintext_password,
            key=self.key,
        )

    def do_get(self, arg: str):
        name: str = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        password = vault.read(username=self.username, name=name, key=self.key)
        if password is None:
            print(f"No password found for '{name}'")
        else:
            print(f"{name}: {password}")

    def do_update(self, arg: str):
        name = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        new_password = getpass.getpass("Password: ")
        if not new_password:
            print("Password cannot be empty")
            return
        vault.update(
            username=self.username, name=name, new_password=new_password, key=self.key
        )

    def do_delete(self, arg: str):
        name = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        vault.delete(username=self.username, name=name)

    do_a = do_add
    do_g = do_get
    do_u = do_update
    do_d = do_delete

    do_exit = do_bye
    do_quit = do_bye
    do_q = do_bye


def list_users() -> None:
    query: str = """SELECT * FROM users;"""
    users = fetchall(query=query)
    for username, _, _ in users:
        print(username)


def main():
    parser = argparse.ArgumentParser(
        description="A local-first CLI password manager with Argon2 hashing and Fernet encryption"
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("signup", help="Create a new user")
    subparsers.add_parser("list", help="List all users")

    parser.add_argument("-u", "--user", default="", help="User logging in")

    args = parser.parse_args()

    init_db()

    username: str
    key: bytes
    if args.command == "list":
        list_users()
        exit(0)

    if args.command == "signup":
        username = input("Username: ")
        plaintext_password: str = getpass.getpass("Password: ")
        if not plaintext_password:
            print("Password cannot be empty")
            exit(1)

        signup_salt: str = signup(username=username, password=plaintext_password)
        key = derive_key(salt=signup_salt, master_password=plaintext_password)

    elif args.command is None and args.user != "":
        username = args.user
        plaintext_password: str = getpass.getpass("Password: ")
        if not plaintext_password:
            print("Password cannot be empty")
            exit(1)

        login_salt: str | None = login(username=args.user, password=plaintext_password)
        if login_salt is None:
            print("Invalid username or password")
            exit(1)
        key = derive_key(salt=login_salt, master_password=plaintext_password)

    else:
        parser.print_help()
        exit(0)

    PassManShell(username=username, key=key).cmdloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{str(e)}")
