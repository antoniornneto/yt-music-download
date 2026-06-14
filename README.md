# Baixar Música do YouTube em MP3

Programa de terminal simples, em Python, para baixar o áudio de vídeos do
YouTube em MP3. Pensado para ser fácil de usar: cole o link, escolha a
qualidade, escolha a pasta e pronto.

## Como instalar (só na primeira vez)

1. Instale o **Python 3.9 ou mais novo**: https://www.python.org/downloads/
   - No Windows, marque a opção **"Add Python to PATH"** durante a instalação.
2. Abra o terminal **dentro da pasta do projeto** e instale as bibliotecas:

   ```
   pip install -r requirements.txt
   ```

   > Não precisa instalar o `ffmpeg` à mão: o programa baixa ele sozinho na
   > primeira vez que roda (por isso a primeira execução demora um pouco mais).

3. **(Recomendado) Instale o Deno**, um pequeno componente que ajuda o
   `yt-dlp` a destravar alguns vídeos do YouTube. No Windows:

   ```
   winget install DenoLand.Deno
   ```

   Depois **feche e abra o terminal de novo** para o sistema reconhecer o Deno.

## Como usar

No terminal, dentro da pasta do projeto:

```
python main.py
```

Depois é só seguir as perguntas na tela.

## Como o projeto está organizado

| Arquivo           | O que faz                                                        |
|-------------------|------------------------------------------------------------------|
| `main.py`         | Junta tudo e controla o passo a passo. É o arquivo que você roda. |
| `ui.py`           | Tudo que aparece na tela: menus, cores, barra de progresso.       |
| `downloader.py`   | O "motor": conversa com o YouTube e gera o MP3.                   |
| `validators.py`   | Verificações: internet, link válido, pasta de destino.           |
| `requirements.txt`| Lista das bibliotecas necessárias.                               |

A ideia dessa separação: cada arquivo cuida de **uma responsabilidade**. Isso
deixa o código mais fácil de ler e de mudar — bom para aprender.

## Solução de problemas

**"This video is not available" (mas o vídeo abre normalmente no navegador)**
Isso costuma acontecer quando o YouTube recusa os "clientes" padrão do `yt-dlp`
para aquele vídeo. O programa já tenta vários clientes automaticamente (incluindo
o `android`, que resolve a maioria desses casos). Se ainda assim falhar:

1. Atualize o `yt-dlp`: `pip install -U yt-dlp`
2. Confirme que o **Deno** está instalado (veja o passo 3 da instalação).

**O nome do arquivo tem um `：` esquisito no lugar do `:`**
É normal: o Windows não permite `:` em nomes de arquivo, então o `yt-dlp` troca
por um caractere parecido. O MP3 funciona normalmente.

## Aviso

Use apenas para baixar conteúdo que você tem o direito de baixar (ex.: vídeos
próprios ou com licença que permita). Respeite os termos de uso do YouTube e os
direitos autorais.
