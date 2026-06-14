"""
validators.py
-------------
Aqui ficam as funcoes que VERIFICAM coisas antes de tentarmos baixar.

A ideia: "falhar cedo e com mensagem clara". E melhor avisar o usuario
logo no comeco ("voce esta sem internet") do que deixar o programa quebrar
no meio do download com um erro tecnico assustador.

Cada funcao faz UMA coisa so e devolve um valor simples (True/False ou um
caminho), sem imprimir nada na tela. Quem imprime e o ui.py. Assim mantemos
"regras" separadas de "aparencia".
"""

import re
import socket
from pathlib import Path


# Uma "expressao regular" (regex) e um padrao de texto.
# Aqui dizemos: o link precisa conter um destes trechos para parecer YouTube.
# Cobrimos os 3 formatos mais comuns: youtube.com/watch, youtu.be e shorts.
PADRAO_YOUTUBE = re.compile(
    r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)",
    re.IGNORECASE,  # ignora maiusculas/minusculas
)


def tem_internet(host="8.8.8.8", porta=53, timeout=3):
    """
    Retorna True se houver conexao com a internet, False caso contrario.

    Como funciona: tentamos abrir uma conexao com o servidor de DNS do Google
    (8.8.8.8, porta 53). Se conseguir, ha internet. Nao baixamos nada aqui,
    so testamos a conexao. O 'timeout' evita que o programa fique travado
    esperando para sempre.
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, porta))
        return True
    except OSError:
        # OSError cobre os erros de rede (sem conexao, host inalcancavel, etc.)
        return False


def parece_link_youtube(url):
    """
    Retorna True se o texto colado PARECE um link do YouTube.

    Atencao: isso e so uma checagem rapida de formato. Nao garante que o video
    exista (isso so descobrimos ao consultar o YouTube de fato, no downloader).
    Serve para barrar erros obvios, tipo o usuario colar um link da Netflix.
    """
    if not url:
        return False
    return bool(PADRAO_YOUTUBE.search(url.strip()))


def preparar_pasta(caminho):
    """
    Recebe um caminho de pasta (texto) e garante que ela exista.

    - expanduser() transforma "~" no caminho real da sua pasta de usuario.
    - mkdir(parents=True, exist_ok=True) cria a pasta (e as pastas-mae que
      faltarem). Se ja existir, nao reclama.

    Retorna o caminho pronto como um objeto Path. Se nao for possivel criar
    (ex.: sem permissao), o erro "sobe" para quem chamou tratar.
    """
    pasta = Path(caminho).expanduser()
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta
