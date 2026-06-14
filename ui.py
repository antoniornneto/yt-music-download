"""
ui.py  (UI = User Interface, "interface com o usuario")
------------------------------------------------------
Tudo que aparece na TELA fica aqui: textos, cores, menus, perguntas e a barra
de progresso.

Usamos DUAS bibliotecas, cada uma no que faz melhor:
- 'questionary' -> as PERGUNTAS navegaveis pelas setas do teclado (escolher
  qualidade, responder Sim/Nao). O usuario nao precisa digitar numero nem y/n:
  so usa as setas e aperta Enter.
- 'rich' -> as MENSAGENS bonitas (cores, caixas, barra de progresso).

Por que separar tudo isso do resto do programa? Porque assim o "motor"
(downloader.py) nao precisa saber nada sobre aparencia, e a parte visual fica
toda num lugar so. Se um dia voce quiser mudar o visual, mexe so aqui.
"""

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
)

# O 'console' e o objeto do rich que usamos para imprimir com cores.
# Criamos UM so e reaproveitamos em todas as funcoes.
console = Console()


def _perguntar(pergunta_questionary):
    """
    Funcao auxiliar usada por todas as perguntas.

    O questionary devolve None se o usuario apertar Ctrl+C para cancelar.
    Aqui transformamos esse None em KeyboardInterrupt, que o main.py ja sabe
    tratar (encerra o programa com elegancia). Assim nao precisamos repetir
    essa verificacao em cada pergunta.
    """
    resposta = pergunta_questionary.ask()
    if resposta is None:
        raise KeyboardInterrupt
    return resposta


def banner():
    """Mostra o titulo do programa logo que ele abre."""
    console.print(
        Panel.fit(
            "[bold green]Baixar Musica do YouTube em MP3[/bold green]\n"
            "[dim]Use as setas ↑ ↓ para escolher e Enter para confirmar.[/dim]",
            border_style="green",
        )
    )


# --- Funcoes de mensagem: atalhos curtos para cada "tom" de aviso ---------

def sucesso(texto):
    console.print(f"[bold green]✓[/bold green] {texto}")  # ✓ = check


def erro(texto):
    console.print(f"[bold red]✗[/bold red] {texto}")      # ✗ = X


def aviso(texto):
    console.print(f"[bold yellow]![/bold yellow] {texto}")


def info(texto):
    console.print(f"[cyan]•[/cyan] {texto}")               # • = bolinha


# --- Perguntas ao usuario (navegadas pelas setas) --------------------------

def pedir_link():
    """Pergunta o link do video e devolve o texto digitado (sem espacos)."""
    resposta = _perguntar(
        questionary.text("Cole o link do video do YouTube:")
    )
    return resposta.strip()


def escolher_qualidade():
    """
    Mostra um menu de qualidades navegavel pelas setas e devolve o bitrate.

    Cada 'Choice' tem um texto (o que o usuario le) e um 'value' (o que o
    programa usa internamente, ex.: "192"). O cursor ja comeca no recomendado.
    """
    opcoes = [
        questionary.Choice("128 kbps  — arquivo menor, qualidade boa", value="128"),
        questionary.Choice("192 kbps  — recomendado", value="192"),
        questionary.Choice("320 kbps  — melhor qualidade, arquivo maior", value="320"),
    ]
    return _perguntar(
        questionary.select(
            "Escolha a qualidade do audio:",
            choices=opcoes,
            default=opcoes[1],  # comeca apontando para "192 kbps (recomendado)"
        )
    )


def escolher_pasta(pasta_padrao):
    """
    Pergunta a pasta de destino, ja sugerindo uma pasta padrao.

    Usamos questionary.path, que ajuda a completar caminhos com a tecla Tab.
    Se o usuario so apertar Enter, fica com a pasta padrao. Devolvemos o texto
    do caminho (a criacao/validacao acontece depois, no validators.py).
    """
    resposta = _perguntar(
        questionary.path(
            "Pasta onde salvar (Enter para usar a sugerida):",
            default=str(pasta_padrao),
            only_directories=True,  # sugere apenas pastas, nao arquivos
        )
    )
    return resposta.strip()


def confirmar(titulo, bitrate, pasta):
    """
    Mostra um resumo (video, qualidade, pasta) e pede confirmacao Sim/Nao.

    Em vez de digitar y/n, o usuario escolhe "Sim" ou "Nao" com as setas.
    Retorna True se confirmar, False se quiser cancelar.
    """
    console.print(
        Panel(
            f"[bold]Video:[/bold] {titulo}\n"
            f"[bold]Qualidade:[/bold] {bitrate} kbps\n"
            f"[bold]Salvar em:[/bold] {pasta}",
            title="Confirme antes de baixar",
            border_style="cyan",
        )
    )
    resposta = _perguntar(
        questionary.select(
            "Pode baixar?",
            choices=["Sim", "Não"],
            default="Sim",
        )
    )
    return resposta == "Sim"


def perguntar_outro():
    """Pergunta (com setas) se o usuario quer baixar outra musica. True/False."""
    resposta = _perguntar(
        questionary.select(
            "Deseja baixar outra musica?",
            choices=["Não", "Sim"],
            default="Não",
        )
    )
    return resposta == "Sim"


# --- Barra de progresso ----------------------------------------------------

class BarraDeProgresso:
    """
    Cuida da barra de progresso durante o download.

    Funciona como um "gerenciador de contexto" (usado com 'with'), para que a
    barra apareca ao entrar no bloco e desapareca de forma limpa ao sair.

    O metodo .hook e o que entregamos ao yt-dlp: ele chama essa funcao varias
    vezes por segundo, passando um dicionario 'd' com o andamento do download.
    """

    def __init__(self):
        # Montamos a barra com varias "colunas": texto, barra, tamanho e velocidade.
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
        )
        self.task_id = None  # id da "tarefa" da barra; criado no primeiro hook

    def __enter__(self):
        self.progress.start()
        return self

    def __exit__(self, *args):
        self.progress.stop()

    def hook(self, d):
        """Chamado pelo yt-dlp. 'd' tem o status e os bytes baixados."""
        if d["status"] == "downloading":
            # O tamanho total as vezes vem exato, as vezes so estimado.
            total = d.get("total_bytes") or d.get("total_bytes_estimate")

            # Criamos a barra na primeira vez que sabemos o total.
            if self.task_id is None and total:
                self.task_id = self.progress.add_task("Baixando", total=total)

            if self.task_id is not None and total:
                self.progress.update(
                    self.task_id,
                    completed=d.get("downloaded_bytes", 0),
                )

        elif d["status"] == "finished":
            # Download terminou; agora o ffmpeg vai converter para MP3.
            if self.task_id is not None:
                self.progress.update(self.task_id, description="Baixado")
            console.print("[cyan]•[/cyan] Convertendo para MP3...")
