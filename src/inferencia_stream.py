"""
inferencia_stream.py
--------------------
Trabalho 3ª Etapa – Inteligência Artificial (UNIPAC Barbacena)
Parte 2, item 3: Automação de inferência via Python (streaming).

Versão revisada do script base do professor. A lógica original foi mantida
(requests.post com stream=True, leitura linha a linha com iter_lines() e
parada pelo campo "done"). Foram acrescentados:
  1. timeout na requisição;
  2. tratamento do campo "error" devolvido pelo Ollama;
  3. métricas finais: eval_count e tokens/s calculado a partir de eval_duration.
"""

import json
import sys

import requests

# Evita erro de codificação no console do Windows caso o modelo gere algum
# caractere que a página de código do terminal não consiga exibir.
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

# URL do endpoint local do Ollama
URL = "http://localhost:11434/api/generate"

# Timeout no formato (conexão, leitura), em segundos.
# - conexão: quanto esperar para abrir a conexão com o servidor;
# - leitura: quanto esperar ENTRE dois pedaços de dados. No streaming, cada
#   token "zera" esse relógio; o valor alto cobre o carregamento inicial do
#   modelo na memória, que pode demorar na primeira chamada.
TIMEOUT = (10, 300)

# Configuração do payload (corpo da requisição)
payload = {
    "model": "llama3.1:8b",  # Modelo já baixado no Ollama (ver "ollama list")
    "prompt": (
        "Escreva um algoritmo de ordenação Bubble Sort em C bem documentado."
    ),
    "options": {
        "temperature": 0.2,  # Baixa temperatura para maior precisão lógica
        "top_p": 0.9,  # Corte dinâmico de probabilidade (nucleus sampling)
        "num_predict": 300,  # Limite máximo de tokens gerados
    },
    "stream": True,  # Crucial para receber token por token em tempo real
}


def extrair_erro(resposta):
    """Tenta ler a mensagem do campo "error" no corpo de uma resposta HTTP."""
    try:
        return resposta.json().get("error", resposta.text)
    except ValueError:
        return resposta.text


def exibir_metricas(data):
    """Mostra as métricas que o Ollama envia no último chunk (done=True)."""
    eval_count = data.get("eval_count", 0)          # tokens gerados
    eval_duration_ns = data.get("eval_duration", 0)  # tempo de geração (ns)
    total_ns = data.get("total_duration", 0)         # tempo total (ns)
    load_ns = data.get("load_duration", 0)           # carga do modelo (ns)

    # O Ollama mede os tempos em NANOSSEGUNDOS: 1 s = 1e9 ns.
    eval_s = eval_duration_ns / 1e9
    tokens_por_s = eval_count / eval_s if eval_s > 0 else 0.0

    print("\n\n--- Geração Concluída ---")
    print(f"Motivo da parada (done_reason): {data.get('done_reason', 'n/d')}")
    print(f"Tokens do prompt (prompt_eval_count): {data.get('prompt_eval_count', 0)}")
    print(f"Total de tokens gerados (eval_count): {eval_count}")
    print(f"Tempo de geração (eval_duration): {eval_s:.2f} s")
    print(f"Velocidade: {tokens_por_s:.2f} tokens/s")
    print(f"Tempo de carga do modelo (load_duration): {load_ns / 1e9:.2f} s")
    print(f"Tempo total (total_duration): {total_ns / 1e9:.2f} s")


def main():
    try:
        # Dispara a requisição mantendo a conexão aberta (stream=True)
        response = requests.post(URL, json=payload, stream=True, timeout=TIMEOUT)

        # Se o Ollama recusou o pedido (ex.: modelo inexistente -> HTTP 404),
        # o corpo traz {"error": "..."}. Mostramos essa mensagem, que é mais
        # útil que o erro HTTP genérico do raise_for_status().
        if response.status_code != 200:
            print(f"Erro do Ollama (HTTP {response.status_code}): {extrair_erro(response)}")
            return

        print("--- Iniciando Geração do Modelo (Streaming) ---\n")

        # Itera sobre cada linha (chunk) recebida no fluxo.
        # Cada linha é um objeto JSON independente (formato NDJSON).
        for chunk in response.iter_lines():
            if not chunk:
                continue

            # Decodifica o JSON retornado pelo Ollama
            data = json.loads(chunk.decode("utf-8"))

            # Um erro também pode chegar NO MEIO do fluxo (ex.: falta de memória)
            if "error" in data:
                print(f"\n\nErro do Ollama durante a geração: {data['error']}")
                return

            # Extrai o texto do token atual e imprime sem quebra de linha
            token_text = data.get("response", "")
            print(token_text, end="", flush=True)

            # Verifica se o modelo concluiu a geração
            if data.get("done", False):
                exibir_metricas(data)
                break

    except requests.exceptions.ConnectionError:
        print(
            "Erro: Não foi possível conectar ao Ollama. Verifique se o serviço "
            "está rodando localmente (ollama serve)."
        )
    except requests.exceptions.Timeout:
        print(
            f"Erro: o Ollama não respondeu dentro do tempo limite {TIMEOUT} s. "
            "O modelo pode estar carregando ou a máquina está sobrecarregada."
        )
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
