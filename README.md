# Trabalho 3ª Etapa – Inteligência Artificial

**UNIPAC Barbacena · Ciência da Computação · Prof. Felipe Roncalli de Paula Carneiro**

Pesquisa teórica (RNN → Transformers → LLMs) e laboratório prático de inferência local com **Ollama** e **Python** (streaming de tokens, controle de hiperparâmetros e experimento de temperatura).

## Objetivo

- **Parte 1:** relatório dissertativo sobre o gargalo sequencial das RNNs, a arquitetura Transformer, o mecanismo Q/K/V e a linha de montagem de um LLM (tokenização, pré-treinamento, SFT e RLHF × DPO).
- **Parte 2:** executar um LLM quantizado (GGUF) localmente com o Ollama, consumir a API `/api/generate` com `stream=True`, expandir o script com controle de `top_p` e `num_predict` e salvamento em `.txt`, e comparar três cenários de temperatura.

## Estrutura

```
trabalho-etapa-3/
├── README.md
├── requirements.txt
├── src/
│   ├── inferencia_stream.py        # Parte 2.3 – script base revisado (streaming + métricas)
│   ├── inferencia_cli.py           # Parte 2.4 – desafio: argparse + validação + .txt
│   └── experimento_temperatura.py  # Parte 2.2 – cenários A/B/C, 2 repetições cada
├── saidas/                         # .txt (e .c) gerados automaticamente
├── evidencias/                     # prints de tela do setup do Ollama
└── relatorio/                      # relatório final em PDF
```

## Requisitos e instalação

- Windows 11 (testado), Python 3.8+ e [Ollama](https://ollama.com/download) instalado.
- Modelo usado: `llama3.1:8b` (pesos quantizados em GGUF; o nível de quantização aparece em `ollama show llama3.1:8b`).

```bash
ollama pull llama3.1:8b      # baixa o modelo (≈4,9 GB)
ollama list                  # confirma o download
ollama show llama3.1:8b      # mostra arquitetura, parâmetros e quantização
pip install -r requirements.txt
```

Teste rápido da API (PowerShell):

```powershell
curl.exe http://localhost:11434/api/generate -d '{\"model\":\"llama3.1:8b\",\"prompt\":\"Diga ola\",\"stream\":false}'
```

## Como rodar

Execute os comandos a partir da raiz do projeto (`trabalho-etapa-3/`).

### 1. Script base com streaming

```bash
python src/inferencia_stream.py
```

Mostra os tokens em tempo real e, no fim, `eval_count`, a velocidade em tokens/s (`eval_count / eval_duration × 10⁹`) e o motivo da parada.

### 2. Desafio: hiperparâmetros pela linha de comando

```bash
python src/inferencia_cli.py --temperature 0.2 --top_p 0.9 --num_predict 300
python src/inferencia_cli.py --prompt "Explique recursão em Python" --top_p 0.5 --num_predict 150 --seed 42
python src/inferencia_cli.py --help
```

| Argumento | Padrão | Faixa válida |
|---|---|---|
| `--prompt` | Bubble Sort em C | texto |
| `--modelo` | `llama3.1:8b` | qualquer modelo do `ollama list` |
| `--temperature` | 0.2 | ≥ 0 |
| `--top_p` | 0.9 | 0 < top_p ≤ 1 |
| `--num_predict` | 300 | > 0 |
| `--seed` | (nenhuma) | inteiro |

Valores fora da faixa são recusados pelo `argparse` com uma mensagem explicativa. A resposta é salva em `saidas/AAAAMMDD_HHMMSS_<modelo>_T<temp>_P<top_p>_N<num_predict>[_S<seed>].txt`, com um cabeçalho que traz o modelo, o prompt, os hiperparâmetros, a data e as métricas.

**No PyCharm:** abra *Run → Edit Configurations… → + → Python*, escolha `src/inferencia_cli.py` em *Script path*, coloque os argumentos em *Parameters* (ex.: `--temperature 0.2 --top_p 0.9 --num_predict 300`) e defina *Working directory* como a raiz do projeto.

### 3. Experimento de temperatura

```bash
python src/experimento_temperatura.py
```

| Cenário | temperature | top_p | Objetivo |
|---|---|---|---|
| A | 0.0 | 1.0 | determinismo (argmax) |
| B | 0.9 | 0.9 | criatividade controlada |
| C | 1.5 | 1.0 | cauda longa / colapso |

Cada cenário roda 2 vezes com o mesmo prompt e `num_predict = 800`. O script gera um `.txt` e um `.c` (o código extraído) por execução e um `*_experimento_resumo.txt` com as métricas, a comparação entre as repetições e o teste de compilação com `gcc`, se ele estiver instalado.

## Autor

Lucas Eduardo Silva
