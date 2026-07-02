import argparse
import getpass

from pathlib import Path
from datetime import datetime

import shlex

import json

from importlib.metadata import version

import cmd
from typing import IO

from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

from passman.auth import signup, login

from passman.crypto import derive_key

from passman.database import fetchall

from passman.schema import init_db

import passman.vault as vault

import passman.generator as generator


class GenArgParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _build_gen_parser() -> GenArgParser:
    parser = GenArgParser(prog="gen", add_help=False)
    parser.add_argument("name")
    parser.add_argument("description", nargs="?", default=None)
    parser.add_argument("-l", "--length", type=int, default=16)
    parser.add_argument("-S", "--no-symbols", action="store_true")
    parser.add_argument("-D", "--no-digits", action="store_true")
    return parser


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

    json_schema: dict = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "password": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["name", "password"],
        },
    }

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

    def do_bye(self, arg: str) -> bool:
        """Exit the shell."""
        print("Exiting...")
        return True

    def do_add(self, arg: str):
        """Add a new password: (a)dd <name>"""
        name = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        plaintext_password: str = getpass.getpass("Password: ")
        if not plaintext_password:
            print("Password cannot be empty")
            return

        description = input("Add description: ")

        vault.create(
            username=self.username,
            name=name,
            plaintext_password=plaintext_password,
            key=self.key,
            description=description or None,
        )

    def do_get(self, arg: str):
        """Retrieve a password: (g)et <name>"""
        name: str = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        result = vault.read(username=self.username, name=name, key=self.key)
        if not result:
            print(f"No password found for '{name}'")
            return
        password, description = result
        print(f"Name        : {name}")
        print(f"Password    : {password}")
        print(f"Description : {description if description else '-'}")

    def do_update(self, arg: str):
        """Update an existing password: (u)pdate <name>"""
        name = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        new_password = getpass.getpass("Password: ")
        description = input("Update description: ")

        if not new_password:
            print("Password cannot be empty")
            return
        vault.update(
            username=self.username,
            name=name,
            new_password=new_password,
            key=self.key,
            description=description or None,
        )

    def do_delete(self, arg: str):
        """Delete a password: (d)elete <name>"""
        name = arg.strip()
        if not name:
            print("Empty field not allowed")
            return
        vault.delete(username=self.username, name=name)

    def do_list(self, arg: str):
        """List all saved password names: (l)ist"""
        query: str = """SELECT name, description FROM passwords WHERE username=?"""
        params: tuple[str, ...] = (self.username,)
        rows = fetchall(query=query, params=params)
        if not rows:
            print("No passwords saved")
            return
        for name, description in rows:
            desc = description if description else "-"
            print(f"{name:<20} {desc}")

    def do_export(self, arg: str):
        """Export passwords to a JSON file: export [path]"""
        directory: str = arg.strip()
        if not directory:
            directory = str(Path.cwd())
        if not Path(directory).is_dir():
            print(f"'{directory}' does not exist")
            return

        now = datetime.now()
        formatted_date: str = now.strftime("%d-%m-%Y")
        formatted_time: str = now.strftime("%H-%M-%S")
        output_file = (
            Path(directory)
            / f"passman-{self.username}-{formatted_date}-{formatted_time}.json"
        )

        query: str = """SELECT username, name FROM passwords WHERE username=?"""
        params: tuple[str, ...] = (self.username,)
        rows = fetchall(query=query, params=params)

        if not rows:
            print("No data found!")
            return

        passwords: list[dict[str, str]] = []
        for _, name in rows:
            result = vault.read(username=self.username, name=name, key=self.key)
            if not result:
                continue
            password, description = result
            passwords.append(
                {"name": name, "password": password, "description": description}
            )

        with open(output_file, "w") as f:
            json.dump(passwords, f, indent=2)

        print(f"Passwords exported to {output_file}")

    def do_import(self, arg: str):
        """Import passwords from a JSON file: import <path>"""
        filename = arg.strip()

        if not filename:
            print("Enter a valid filename")
            return

        if not (FILE := Path(filename)).exists():
            print(f"'{filename}' does not exist")
            return

        if FILE.suffix != ".json":
            print("Not a JSON file")
            return

        with open(FILE, "r") as f:
            data = json.load(f)

        try:
            validate(instance=data, schema=self.json_schema)
        except (ValidationError, SchemaError) as e:
            print(f"Invalid JSON format in {filename} : {e.message}")
            return

        skipped = 0
        imported = 0
        for entry in data:
            name = entry.get("name")
            password = entry.get("password")
            description = entry.get("description")

            existing = vault.read(username=self.username, name=name, key=self.key)

            if existing is not None:
                response = input(
                    f"Entry with '{name}' already exists. Do you want to over-write it? [Y]es/[N]o: "
                )
                if not response:
                    print("Invalid input.")
                    skipped += 1
                    continue
                elif response.lower() in ("y", "yes"):
                    vault.update(
                        username=self.username,
                        name=name,
                        new_password=password,
                        key=self.key,
                        description=description,
                    )
                    imported += 1
                    continue
                elif response.lower() in ("n", "no"):
                    skipped += 1
                    continue
                else:
                    print("Invalid input.")
                    skipped += 1
                    continue

            vault.create(
                username=self.username,
                name=name,
                plaintext_password=password,
                key=self.key,
                description=description,
            )
            imported += 1

        print(
            f"Imported {imported} password(s), skipped {skipped} existing entr{'y' if skipped == 1 else 'ies'} from {filename}"
        )

    def do_gen(self, arg: str):
        """gen <name> [description] [-l LENGTH] [-S] [-D]"""
        try:
            args = _build_gen_parser().parse_args(shlex.split(arg))
            if args.length < 8:
                raise ValueError("Password length must be at least 8")

            existing = vault.read(username=self.username, name=args.name, key=self.key)

            if existing is not None:
                response = input(
                    f"Entry with '{args.name}' already exists. Do you want to over-write it? [Y]es/[N]o: "
                )
                if response.lower() not in ("y", "yes"):
                    print(f"Not generating password for '{args.name}'")
                    return

            generated_password: str = generator.generate_password(
                length=args.length,
                use_symbols=not args.no_symbols,
                use_digits=not args.no_digits,
            )
            if existing is not None:
                vault.update(
                    username=self.username,
                    name=args.name,
                    new_password=generated_password,
                    description=args.description,
                    key=self.key,
                )
            else:
                vault.create(
                    username=self.username,
                    name=args.name,
                    plaintext_password=generated_password,
                    description=args.description,
                    key=self.key,
                )
            print(f"Generated and saved password for '{args.name}'")

        except ValueError as e:
            print(f"Error: {e}")
            return

    do_a = do_add
    do_g = do_get
    do_u = do_update
    do_d = do_delete
    do_l = do_list

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

    parser.add_argument(
        "-v", "--version", action="version", version=f"PassMan v{version('passman')}"
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
