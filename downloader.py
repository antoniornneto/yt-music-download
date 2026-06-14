"""
downloader.py
-------------
O "motor" do programa: tudo que fala com o YouTube fica aqui.

Usamos a biblioteca yt-dlp. Ela faz o trabalho pesado (achar o audio, baixar
e, com a ajuda do ffmpeg, converter para MP3 na qualidade escolhida).

Importante para aprender:
- Este arquivo NAO imprime menus nem cores. Ele so baixa e, se algo der errado,
  levanta um erro nosso (DownloadError) com uma mensagem simples.
- Quem mostra as coisas para o usuario e o ui.py / main.py. Manter essa
  separacao deixa o codigo mais facil de entender e de testar.
"""

from pathlib import Path

import yt_dlp


# Dicionario que liga a opcao do menu (1, 2, 3) ao bitrate em kbps.
# bitrate maior = mais qualidade e arquivo maior.
# Deixamos isso aqui (e nao "solto" no codigo) para ser facil de mudar depois.
QUALIDADES = {
    "1": "128",  # leve
    "2": "192",  # recomendado
    "3": "320",  # melhor qualidade
}


# O YouTube oferece o video atraves de varios "clientes" (o app de Android, o
# site, a Smart TV, etc.). De tempos em tempos ele recusa alguns clientes e so
# entrega o video por outros. Por isso pedimos ao yt-dlp para TENTAR varios:
# se um falhar, ele usa outro. O 'android' costuma funcionar quando os demais
# sao bloqueados; deixamos ele na lista por seguranca.
CLIENTES_YOUTUBE = ["android", "web", "ios", "mweb"]

# Opcoes que valem para QUALQUER chamada ao yt-dlp. Definimos uma vez so e
# reaproveitamos, para nao repetir (e nao esquecer de manter igual nos dois lugares).
OPCOES_BASE = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "extractor_args": {"youtube": {"player_client": CLIENTES_YOUTUBE}},
}


class DownloadError(Exception):
    """
    Nosso erro "amigavel".

    O yt-dlp solta erros bem tecnicos. Em vez de deixar esses erros vazarem
    para o usuario, nos os capturamos e levantamos este DownloadError com uma
    mensagem mais simples. Assim o main.py so precisa lidar com UM tipo de erro.
    """
    pass


def obter_info(url):
    """
    Consulta o YouTube e devolve os dados do video (titulo, duracao, etc.)
    SEM baixar nada (download=False).

    Servem para dois objetivos:
    1) Confirmar que o video realmente existe e esta disponivel.
    2) Mostrar o titulo na tela de confirmacao antes de baixar.

    Se o video nao existir, for privado ou removido, o yt-dlp solta um erro,
    que convertemos em DownloadError.
    """
    # Partimos das opcoes base (que ja incluem a lista de clientes do YouTube).
    opcoes = dict(OPCOES_BASE)
    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            return ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        # Repassamos a mensagem original dentro do nosso erro amigavel.
        raise DownloadError(str(e))


def baixar_audio(url, bitrate, pasta_destino, pasta_ffmpeg=None, progress_hook=None):
    """
    Baixa o audio do video e converte para MP3.

    Parametros:
    - url: o link do video.
    - bitrate: a qualidade em kbps como texto, ex.: "192".
    - pasta_destino: onde salvar (objeto Path ou texto).
    - pasta_ffmpeg: a PASTA onde estao o ffmpeg.exe e o ffprobe.exe. Informar
      isso ao yt-dlp (via "ffmpeg_location") garante que a conversao para MP3
      funcione mesmo dentro do executavel, onde depender do PATH nao era
      confiavel. Se for None, o yt-dlp procura o ffmpeg sozinho no PATH.
    - progress_hook: uma funcao opcional que o yt-dlp chama varias vezes
      durante o download, informando o progresso. Usamos isso para mover a
      barra de progresso. (Veremos no ui.py.)

    Nao retorna nada em caso de sucesso. Em caso de falha, levanta DownloadError.
    """
    # O "outtmpl" e o modelo do nome do arquivo de saida.
    # %(title)s vira o titulo do video e %(ext)s a extensao.
    modelo_nome = str(Path(pasta_destino) / "%(title)s.%(ext)s")

    opcoes = dict(OPCOES_BASE)
    opcoes.update({
        # "bestaudio/best": pega a melhor faixa de audio disponivel.
        "format": "bestaudio/best",
        "outtmpl": modelo_nome,
        # Os "postprocessors" rodam DEPOIS do download.
        # FFmpegExtractAudio usa o ffmpeg para extrair/converter o audio em MP3.
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }
        ],
    })

    # Se sabemos onde o ffmpeg esta, dizemos isso explicitamente ao yt-dlp.
    if pasta_ffmpeg:
        opcoes["ffmpeg_location"] = str(pasta_ffmpeg)

    # So adicionamos o hook se ele foi passado.
    if progress_hook is not None:
        opcoes["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e))
