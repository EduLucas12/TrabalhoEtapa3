"""
inferencia_cli.py
-----------------
Trabalho 3ª Etapa – Inteligência Artificial (UNIPAC Barbacena)
Parte 2, item 4: Desafio prático de modificação de código.

Expande o script base com:
  - controle dinâmico dos hiperparâmetros pela linha de comando (argparse):
    --prompt, --modelo, --temperature, --top_p, --num_predict e --seed;
  - validação de faixas: temperature >= 0; 0 < top_p <= 1; num_predict > 0;
  - exibição do streaming no terminal E gravação automática da resposta em
    um arquivo .txt na pasta saidas/, com cabeçalho (modelo, prompt,
    hiperparâmetros, data e métricas).

Exemplo:
    python src/inferencia_cli.py --temperature 0.2 --top_p 0.9 --num_predict 300

As funções gerar_resposta() e salvar_saida() também são reaproveitadas pelo
script experimento_temperatura.py.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

URL_PADRAO = "http://localhost:11434/api/generate"
MODELO_PADRAO = "llama3.1:8b"
PROMPT_PADRAO = "Escreva um algoritmo de ordenação Bubble Sort em C bem documentado."

# Pasta saidas/ na raiz do projeto, independente de onde o script é chamado.
# __file__ = .../trabalho-etapa-3/src/inferencia_cli.py -> parent.parent = raiz
PASTA_SAIDAS = Path(__file__).resolve().parent.parent / "saidas"


class ErroOllama(Exception):
    """Erro informado pelo próprio Ollama (campo "error" da resposta)."""


# ---------------------------------------------------------------------------
# Validação dos argumentos
# ---------------------------------------------------------------------------
# O argparse aceita uma função em "type=". Ela recebe o texto digitado e deve
# devolver o valor convertido ou lançar ArgumentTypeError com a explicação.

def temperatura_valida(texto):
    valor = float(texto)
    if valor < 0:
        raise argparse.ArgumentTypeError("temperature deve ser >= 0.")
    return valor


def top_p_valido(texto):
    valor = float(texto)
    if not 0 < valor <= 1:
        raise argparse.ArgumentTypeError("top_p deve estar no intervalo (0, 1].")
    return valor


def inteiro_positivo(texto):
    valor = int(texto)
    if valor <= 0:
        raise argparse.ArgumentTypeError("num_predict deve ser > 0.")
    return valor


def criar_parser():
    parser = argparse.ArgumentParser(
        description="Inferência local no Ollama com streaming e gravação em .txt."
    )
    parser.add_argument("--prompt", default=PROMPT_PADRAO,
                        help="Texto enviado ao modelo.")
    parser.add_argument("--modelo", default=MODELO_PADRAO,
                        help=f"Modelo do Ollama (padrão: {MODELO_PADRAO}).")
    parser.add_argument("--temperature", type=temperatura_valida, default=0.2,
                        help="Temperatura de amostragem, >= 0 (padrão: 0.2).")
    parser.add_argument("--top_p", type=top_p_valido, default=0.9,
                        help="Nucleus sampling, no intervalo (0, 1] (padrão: 0.9).")
    parser.add_argument("--num_predict", type=inteiro_positivo, default=300,
                        help="Máximo de tokens gerados, > 0 (padrão: 300).")
    parser.add_argument("--seed", type=int, default=None,
                        help="Semente opcional para reprodutibilidade.")
    parser.add_argument("--url", default=URL_PADRAO,
                        help=f"Endpoint do Ollama (padrão: {URL_PADRAO}).")
    parser.add_argument("--timeout", type=inteiro_positivo, default=300,
                        help="Tempo máximo (s) de espera entre dois chunks.")
    return parser


# ---------------------------------------------------------------------------
# Inferência com streaming (mesma lógica do script do professor)
# ---------------------------------------------------------------------------

def gerar_resposta(modelo, prompt, opcoes, url=URL_PADRAO, timeout=300, exibir=True):
    """
    Envia o prompt ao Ollama com stream=True e devolve (texto, metricas).

    - texto: resposta completa, montada concatenando os tokens recebidos;
    - metricas: o último chunk (done=True), que traz eval_count, eval_duration etc.
    Lança ErroOllama se o servidor devolver o campo "error".
    """
    payload = {
        "model": modelo,
        "prompt": prompt,
        "options": opcoes,
        "stream": True,
    }

    response = requests.post(url, json=payload, stream=True, timeout=(10, timeout))

    if response.status_code != 200:
        try:
            mensagem = response.json().get("error", response.text)
        except ValueError:
            mensagem = response.text
        raise ErroOllama(f"HTTP {response.status_code}: {mensagem}")

    partes = []      # lista de tokens; juntar no final é mais eficiente que +=
    metricas = {}

    for chunk in response.iter_lines():
        if not chunk:
            continue
        data = json.loads(chunk.decode("utf-8"))

        if "error" in data:
            raise ErroOllama(data["error"])

        token_text = data.get("response", "")
        partes.append(token_text)
        if exibir:
            print(token_text, end="", flush=True)

        if data.get("done", False):
            metricas = data
            break

    return "".join(partes), metricas


def resumir_metricas(metricas):
    """Converte as métricas brutas (nanossegundos) em valores legíveis."""
    eval_count = metricas.get("eval_count", 0)
    eval_s = metricas.get("eval_duration", 0) / 1e9
    return {
        "done_reason": metricas.get("done_reason", "n/d"),
        "prompt_eval_count": metricas.get("prompt_eval_count", 0),
        "eval_count": eval_count,
        "eval_s": eval_s,
        "tokens_por_s": eval_count / eval_s if eval_s > 0 else 0.0,
        "load_s": metricas.get("load_duration", 0) / 1e9,
        "total_s": metricas.get("total_duration", 0) / 1e9,
    }


# ---------------------------------------------------------------------------
# Gravação do .txt
# ---------------------------------------------------------------------------

def nome_seguro(texto):
    """Troca caracteres proibidos em nomes de arquivo no Windows (ex.: ':')."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", texto)


def salvar_saida(modelo, prompt, opcoes, texto, metricas, inicio,
                 pasta=PASTA_SAIDAS, sufixo=""):
    """Grava cabeçalho + resposta em um .txt e devolve o caminho do arquivo."""
    pasta.mkdir(parents=True, exist_ok=True)

    seed = opcoes.get("seed")
    nome = (
        f"{inicio:%Y%m%d_%H%M%S}_{nome_seguro(modelo)}"
        f"_T{opcoes['temperature']}_P{opcoes['top_p']}_N{opcoes['num_predict']}"
        + (f"_S{seed}" if seed is not None else "")
        + sufixo + ".txt"
    )
    caminho = pasta / nome
    m = resumir_metricas(metricas)
    linha = "=" * 64

    cabecalho = [
        linha,
        "REGISTRO DE INFERÊNCIA – OLLAMA (Trabalho 3ª Etapa)",
        linha,
        f"Data/hora        : {inicio:%d/%m/%Y %H:%M:%S}",
        f"Modelo           : {modelo}",
        f"Prompt           : {prompt}",
        "Hiperparâmetros  :",
        f"  temperature    : {opcoes['temperature']}",
        f"  top_p          : {opcoes['top_p']}",
        f"  num_predict    : {opcoes['num_predict']}",
        f"  seed           : {seed if seed is not None else '(não definida)'}",
        "Métricas         :",
        f"  done_reason    : {m['done_reason']}  (stop = terminou; length = atingiu num_predict)",
        f"  tokens prompt  : {m['prompt_eval_count']}",
        f"  tokens gerados : {m['eval_count']}",
        f"  tempo geração  : {m['eval_s']:.2f} s",
        f"  velocidade     : {m['tokens_por_s']:.2f} tokens/s",
        f"  carga modelo   : {m['load_s']:.2f} s",
        f"  tempo total    : {m['total_s']:.2f} s",
        linha,
        "RESPOSTA COMPLETA",
        linha,
        "",
    ]

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(cabecalho))
        arquivo.write(texto)
        arquivo.write("\n")

    return caminho


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    args = criar_parser().parse_args()

    opcoes = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "num_predict": args.num_predict,
    }
    if args.seed is not None:
        opcoes["seed"] = args.seed

    inicio = datetime.now()
    print(f"Modelo: {args.modelo} | opções: {opcoes}")
    print("--- Iniciando Geração do Modelo (Streaming) ---\n")

    try:
        texto, metricas = gerar_resposta(args.modelo, args.prompt, opcoes,
                                         url=args.url, timeout=args.timeout)
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar ao Ollama. Verifique se o serviço "
              "está rodando localmente (ollama serve).")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Erro: o Ollama não respondeu em {args.timeout} s.")
        sys.exit(1)
    except ErroOllama as e:
        print(f"\nErro do Ollama: {e}")
        sys.exit(1)

    m = resumir_metricas(metricas)
    print("\n\n--- Geração Concluída ---")
    print(f"Tokens gerados: {m['eval_count']} | {m['tokens_por_s']:.2f} tokens/s "
          f"| done_reason: {m['done_reason']}")

    caminho = salvar_saida(args.modelo, args.prompt, opcoes, texto, metricas, inicio)
    print(f"Resposta salva em: {caminho}")


if __name__ == "__main__":
    main()
