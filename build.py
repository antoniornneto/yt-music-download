"""
build.py
--------
Gera o executavel (.exe) de dois cliques, com TUDO embutido.

Para que serve: empacotar o programa num unico arquivo que qualquer pessoa
abre com dois cliques, sem precisar instalar Python nem ffmpeg.

Como usar:

    pip install -r requirements.txt   (so na primeira vez)
    pip install pyinstaller            (so na primeira vez)
    python build.py

No final, o executavel aparece em:  dist/BaixarMusica.exe

----------------------------------------------------------------------------
Por que existe este script (em vez de rodar o PyInstaller na mao)?
O comando do PyInstaller fica longo, porque precisamos dizer a ele onde estao
o ffmpeg.exe e o ffprobe.exe para EMBUTI-LOS no executavel. Este script acha
esses arquivos sozinho e monta o comando certo. Voce so roda "python build.py".
"""

import subprocess
import sys

import PyInstaller.__main__
from static_ffmpeg import run


NOME_DO_APP = "BaixarMusica"


def main():
    # 1) Descobrir onde estao o ffmpeg e o ffprobe.
    #    Se ainda nao foram baixados, esta funcao baixa (precisa de internet).
    print("Localizando o ffmpeg (pode baixar na primeira vez)...")
    ffmpeg_exe, ffprobe_exe = run.get_or_fetch_platform_executables_else_raise()
    print(f"  ffmpeg:  {ffmpeg_exe}")
    print(f"  ffprobe: {ffprobe_exe}")

    # 2) Montar os argumentos do PyInstaller.
    #    No Windows, --add-binary usa o formato  "origem;destino".
    #    O destino "." significa "a raiz de dentro do executavel".
    separador = ";" if sys.platform == "win32" else ":"
    argumentos = [
        "main.py",
        "--name", NOME_DO_APP,
        "--onefile",        # gera UM unico arquivo .exe
        "--console",        # mantem a janela de terminal (precisamos dela p/ os menus)
        "--noconfirm",      # sobrescreve builds anteriores sem perguntar
        "--clean",          # limpa cache de builds antigos
        "--add-binary", f"{ffmpeg_exe}{separador}.",
        "--add-binary", f"{ffprobe_exe}{separador}.",
    ]

    print("\nGerando o executavel... (isso leva alguns minutos)\n")
    PyInstaller.__main__.run(argumentos)

    print(f"\nPronto! O executavel esta em:  dist/{NOME_DO_APP}.exe")


if __name__ == "__main__":
    main()
