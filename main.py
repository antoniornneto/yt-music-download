"""
main.py
-------
Ponto de entrada do programa: e este arquivo que voce roda.

    python main.py

Ele NAO contem a logica de download nem o desenho da tela. O papel dele e
ORGANIZAR o fluxo, chamando na ordem certa as pecas dos outros arquivos:

    validators.py  -> verificacoes (internet, link, pasta)
    ui.py          -> tudo que aparece na tela
    downloader.py  -> conversa com o YouTube

Ler este arquivo de cima a baixo deve dar para entender o programa inteiro.
"""

import os
import sys
from pathlib import Path

# Forca a saida do terminal a usar UTF-8. Sem isso, em consoles antigos do
# Windows (que usam a codificacao cp1252), simbolos como ↑ ↓ ✓ ✗ • fariam o
# programa fechar com erro. Como o publico-alvo e leigo, blindamos logo aqui,
# antes de qualquer texto ser impresso.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # se nao der (ambiente incomum), seguimos mesmo assim

import ui
import validators
from downloader import obter_info, baixar_audio, DownloadError


def preparar_ffmpeg():
    """
    Garante que o ffmpeg esteja disponivel. Ele e um programa externo (nao e
    Python) que faz a conversao para MP3.

    Ha dois jeitos de o programa estar rodando:

    1) Como EXECUTAVEL (.exe gerado pelo PyInstaller): o ffmpeg foi EMBUTIDO no
       proprio exe. Ao abrir, o PyInstaller descompacta tudo numa pasta
       temporaria, cujo caminho fica em sys._MEIPASS. So precisamos avisar o
       sistema (via PATH) que o ffmpeg esta la.

    2) Como SCRIPT ("python main.py"): nao ha nada embutido, entao usamos o
       pacote 'static-ffmpeg', que baixa o ffmpeg na primeira vez e o adiciona
       ao PATH.

    O getattr(sys, "frozen", False) e o jeito padrao de saber se estamos
    rodando "congelados" dentro de um exe.

    RETORNA a PASTA onde estao o ffmpeg.exe e o ffprobe.exe. Esse caminho e
    entregue depois ao yt-dlp (opcao "ffmpeg_location"), o que e mais confiavel
    do que so mexer no PATH: dentro do exe, depender do PATH falhava e a
    conversao para MP3 nao acontecia.
    """
    if getattr(sys, "frozen", False):
        # Dentro do executavel: procuramos o ffmpeg em qualquer lugar do pacote
        # descompactado (sys._MEIPASS), sem supor a subpasta exata. No Windows o
        # binario se chama "ffmpeg.exe"; no macOS e no Linux, apenas "ffmpeg".
        base = Path(sys._MEIPASS)
        nome_ffmpeg = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        achados = list(base.rglob(nome_ffmpeg))
        pasta_ffmpeg = achados[0].parent if achados else base
        # Tambem colocamos no PATH (ajuda o ffprobe a ser encontrado).
        os.environ["PATH"] = str(pasta_ffmpeg) + os.pathsep + os.environ.get("PATH", "")
        return str(pasta_ffmpeg)
    else:
        with ui.console.status("[cyan]Preparando componentes (pode demorar na 1a vez)..."):
            import static_ffmpeg
            from static_ffmpeg import run
            static_ffmpeg.add_paths()
            ffmpeg_exe, _ffprobe = run.get_or_fetch_platform_executables_else_raise()
            return str(Path(ffmpeg_exe).parent)


def pasta_padrao():
    """
    Devolve a pasta sugerida para salvar: Downloads/Musicas do usuario.

    Path.home() e a sua pasta de usuario (ex.: C:\\Users\\Tom). Montamos o
    caminho de forma que funcione em qualquer sistema operacional.
    """
    return Path.home() / "Downloads" / "Musicas"


def baixar_uma_musica(pasta_ffmpeg):
    """
    Executa o fluxo completo de UMA musica, do link ate o arquivo salvo.

    'pasta_ffmpeg' e a pasta onde esta o ffmpeg (descoberta em preparar_ffmpeg),
    repassada ao downloader para a conversao em MP3 funcionar.

    Retorna True se baixou com sucesso, False se algo impediu (e ja avisou o
    usuario). Nao deixa erros "vazarem": tudo vira mensagem amigavel.
    """
    # 1) Pedir e validar o link -------------------------------------------
    url = ui.pedir_link()

    if not validators.parece_link_youtube(url):
        ui.erro("Isso nao parece um link do YouTube. Cole o endereco completo do video.")
        return False

    # 2) Consultar o video (confirma que existe e pega o titulo) ----------
    try:
        with ui.console.status("[cyan]Procurando o video..."):
            info = obter_info(url)
    except DownloadError:
        # Nao mostramos o erro tecnico; damos uma explicacao simples.
        ui.erro("Nao consegui acessar esse video. Ele pode ser privado, ter sido "
                "removido, ou o link esta errado.")
        return False

    titulo = info.get("title", "Audio")

    # 3) Escolher qualidade e pasta ---------------------------------------
    bitrate = ui.escolher_qualidade()
    caminho_escolhido = ui.escolher_pasta(pasta_padrao())

    # Garantimos que a pasta exista (criando se preciso).
    try:
        pasta = validators.preparar_pasta(caminho_escolhido)
    except OSError:
        ui.aviso("Nao consegui usar essa pasta. Vou salvar na pasta padrao.")
        pasta = validators.preparar_pasta(pasta_padrao())

    # 4) Confirmar antes de baixar ----------------------------------------
    if not ui.confirmar(titulo, bitrate, pasta):
        ui.info("Tudo bem, cancelado.")
        return False

    # 5) Baixar de fato, com barra de progresso ---------------------------
    try:
        with ui.BarraDeProgresso() as barra:
            baixar_audio(url, bitrate, pasta, pasta_ffmpeg, progress_hook=barra.hook)
    except DownloadError:
        ui.erro("Algo deu errado durante o download. Verifique sua internet e tente de novo.")
        return False

    ui.sucesso(f"Pronto! Arquivo salvo em: [bold]{pasta}[/bold]")
    return True


def main():
    """Funcao principal: prepara o ambiente e roda o laco do programa."""
    ui.banner()

    # Antes de tudo: tem internet? Sem ela, nada funciona.
    if not validators.tem_internet():
        ui.erro("Voce parece estar sem internet. Conecte-se e abra o programa de novo.")
        return

    # Preparar o ffmpeg. Se falhar, avisamos e encerramos com calma.
    try:
        pasta_ffmpeg = preparar_ffmpeg()
    except Exception:
        ui.erro("Nao consegui preparar o componente de audio (ffmpeg). "
                "Verifique sua internet e tente de novo.")
        return

    # Laco principal: baixa uma musica e pergunta se quer outra.
    while True:
        baixar_uma_musica(pasta_ffmpeg)
        if not ui.perguntar_outro():
            break

    ui.console.print("\n[bold green]Ate a proxima![/bold green]")


def _diagnostico():
    """
    Modo tecnico (nao para o usuario final). Rode "BaixarMusica.exe --diag"
    para verificar se o ffmpeg foi embutido e esta sendo encontrado. Serve
    para depurar problemas sem precisar abrir os menus interativos.
    """
    import shutil

    sufixo = ".exe" if sys.platform == "win32" else ""
    pasta = preparar_ffmpeg()
    print("frozen:", getattr(sys, "frozen", False))
    print("_MEIPASS:", getattr(sys, "_MEIPASS", None))
    print("pasta_ffmpeg retornada:", pasta)
    print("shutil.which('ffmpeg'):", shutil.which("ffmpeg"))
    print("shutil.which('ffprobe'):", shutil.which("ffprobe"))
    print(f"ffmpeg{sufixo} existe na pasta?:", (Path(pasta) / f"ffmpeg{sufixo}").exists())
    print(f"ffprobe{sufixo} existe na pasta?:", (Path(pasta) / f"ffprobe{sufixo}").exists())


# Esta linha faz o programa rodar a funcao main() so quando voce executa
# "python main.py" diretamente (e nao quando outro arquivo o importa).
if __name__ == "__main__":
    if "--diag" in sys.argv:
        _diagnostico()
        sys.exit(0)
    try:
        main()
    except KeyboardInterrupt:
        # Acontece se o usuario apertar Ctrl+C. Saimos sem erro feio.
        ui.console.print("\n[yellow]Encerrado pelo usuario.[/yellow]")
