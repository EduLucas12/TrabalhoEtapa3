"""
experimento_temperatura.py
--------------------------
Trabalho 3ª Etapa – Inteligência Artificial (UNIPAC Barbacena)
Parte 2, item 2: Experimento de hiperparâmetros (temperatura e amostragem).

Roda o MESMO prompt técnico em três cenários, 2 vezes cada:
  A: T = 0.0, top_p = 1.0  -> decodificação gulosa (argmax), determinística
  B: T = 0.9, top_p = 0.9  -> criatividade controlada (nucleus sampling)
  C: T = 1.5, top_p = 1.0  -> cauda longa liberada ("o caos")

top_p = 1.0 em A e C isola o efeito da temperatura (sem corte de núcleo).
num_predict é igual em todos (800) para a comparação ser justa.

Para cada execução gera:
  - um .txt com cabeçalho + resposta (mesmo formato do inferencia_cli.py);
  - um .c com o primeiro bloco de código C encontrado na resposta (se houver);
E, ao final, um arquivo *_experimento_resumo.txt com:
  - métricas de cada execução;
  - se as 2 repetições de cada cenário são idênticas e o % de similaridade;
  - resultado da compilação com gcc (somente se o gcc estiver instalado).
"""

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import requests

# Reaproveita as funções do desafio (mesma pasta src/)
from inferencia_cli import (MODELO_PADRAO, PASTA_SAIDAS, ErroOllama,
                            gerar_resposta, resumir_metricas, salvar_saida)

PROMPT = "Escreva um algoritmo de ordenação Bubble Sort em C bem documentado."
NUM_PREDICT = 800

CENARIOS = [
    # (nome, temperature, top_p)
    ("A", 0.0, 1.0),
    ("B", 0.9, 0.9),
    ("C", 1.5, 1.0),
]


def extrair_codigo_c(texto):
    """Devolve o conteúdo do primeiro bloco ```c ... ``` (ou ``` ... ```)."""
    blocos = re.findall(r"```[ \t]*([A-Za-z+]*)[^\n]*\n(.*?)```", texto, re.DOTALL)
    for linguagem, codigo in blocos:
        if linguagem.lower() in ("c", ""):
            return codigo
    return None


def testar_compilacao(caminho_c):
    """Compila com gcc, se existir. Devolve um texto curto com o resultado."""
    gcc = shutil.which("gcc")
    if gcc is None:
        return "não testado (gcc não encontrado)"
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "teste.exe"
        proc = subprocess.run([gcc, str(caminho_c), "-o", str(saida)],
                              capture_output=True, text=True)
    if proc.returncode == 0:
        return "compilou"
    primeira = (proc.stderr.strip().splitlines() or ["erro"])[0]
    return f"NÃO compilou ({primeira[:120]})"


def main():
    parser = argparse.ArgumentParser(description="Experimento de temperatura A/B/C.")
    parser.add_argument("--modelo", default=MODELO_PADRAO)
    parser.add_argument("--repeticoes", type=int, default=2)
    args = parser.parse_args()

    inicio_exp = datetime.now()
    resultados = []   # um dicionário por execução
    textos = {}       # textos[(cenario, rep)] = resposta

    for nome, temperatura, top_p in CENARIOS:
        for rep in range(1, args.repeticoes + 1):
            opcoes = {"temperature": temperatura, "top_p": top_p,
                      "num_predict": NUM_PREDICT}
            print("\n" + "#" * 64)
            print(f"# Cenário {nome} | T={temperatura} | top_p={top_p} | repetição {rep}")
            print("#" * 64 + "\n")

            inicio = datetime.now()
            try:
                texto, metricas = gerar_resposta(args.modelo, PROMPT, opcoes)
            except requests.exceptions.ConnectionError:
                print("Erro: Ollama não está rodando (ollama serve).")
                sys.exit(1)
            except (requests.exceptions.Timeout, ErroOllama) as e:
                print(f"\nFalha nesta execução: {e}")
                continue

            sufixo = f"_cenario{nome}_rep{rep}"
            caminho_txt = salvar_saida(args.modelo, PROMPT, opcoes, texto,
                                       metricas, inicio, sufixo=sufixo)

            codigo = extrair_codigo_c(texto)
            if codigo:
                caminho_c = caminho_txt.with_suffix(".c")
                caminho_c.write_text(codigo, encoding="utf-8")
                compilacao = testar_compilacao(caminho_c)
            else:
                compilacao = "sem bloco de código C na resposta"

            textos[(nome, rep)] = texto
            m = resumir_metricas(metricas)
            resultados.append({"cenario": nome, "rep": rep, "T": temperatura,
                               "top_p": top_p, "arquivo": caminho_txt.name,
                               "compilacao": compilacao, **m})
            print(f"\n\n[salvo] {caminho_txt.name} | compilação: {compilacao}")

    # ---------------- Resumo ----------------
    linhas = [
        "=" * 64,
        "RESUMO DO EXPERIMENTO DE TEMPERATURA",
        "=" * 64,
        f"Data/hora : {inicio_exp:%d/%m/%Y %H:%M:%S}",
        f"Modelo    : {args.modelo}",
        f"Prompt    : {PROMPT}",
        f"num_predict: {NUM_PREDICT}",
        "",
        "Execuções:",
    ]
    for r in resultados:
        linhas.append(
            f"  {r['cenario']}{r['rep']} | T={r['T']} top_p={r['top_p']} | "
            f"tokens={r['eval_count']} | {r['tokens_por_s']:.2f} tok/s | "
            f"done_reason={r['done_reason']} | {r['compilacao']}"
        )
        linhas.append(f"       arquivo: {r['arquivo']}")

    linhas += ["", "Repetibilidade (rep1 x rep2):"]
    for nome, _, _ in CENARIOS:
        if (nome, 1) in textos and (nome, 2) in textos:
            t1, t2 = textos[(nome, 1)], textos[(nome, 2)]
            ratio = difflib.SequenceMatcher(None, t1, t2).ratio() * 100
            linhas.append(f"  Cenário {nome}: idênticas = {'SIM' if t1 == t2 else 'NÃO'} | "
                          f"similaridade = {ratio:.1f}%")

    resumo = "\n".join(linhas) + "\n"
    caminho_resumo = PASTA_SAIDAS / f"{inicio_exp:%Y%m%d_%H%M%S}_experimento_resumo.txt"
    caminho_resumo.write_text(resumo, encoding="utf-8")
    print("\n\n" + resumo)
    print(f"Resumo salvo em: {caminho_resumo}")


if __name__ == "__main__":
    main()
