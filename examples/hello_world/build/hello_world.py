import os
import typer
from datetime import datetime


app = typer.Typer()


def get_name(name_file: str) -> str:
    with open(name_file) as file_stream:
        return file_stream.read().strip()


def get_greeting_message(chat_file: str) -> str:
    return "Nice to meet you."


@app.command()
def hello(name_file: str = typer.Option(..., '--name'), chat_file: str = typer.Option(..., '--chat')):
    with open(chat_file, 'a') as chat_stream:
        chat_stream.write('[{}]  Hi, {}! {}\n'.format(
            datetime.now(),
            get_name(name_file),
            get_greeting_message(chat_file)
        ))


@app.command()
def bye(name_file: str = typer.Option(..., '--name'), chat_file: str = typer.Option(..., '--chat')):
    with open(chat_file, 'a') as chat_stream:
        chat_stream.write('[{}]  Bye, {}! It was great talking to you.\n'.format(datetime.now(), get_name(name_file)))


if __name__ == '__main__':
    app()
