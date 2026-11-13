# Portfolio Value-at-Risk Calculator

[![CI](https://github.com/Yusa172/Portfolio-Value-at-Risk-Calculator/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Yusa172/Portfolio-Value-at-Risk-Calculator/actions/workflows/ci.yml)

Biblioteca em Python para medir o risco de mercado de uma carteira de ativos através do **Value-at-Risk (VaR)** e do **Expected Shortfall (ES)**. O objetivo é reunir, num só pacote testado e documentado, os métodos mais usados na prática (histórico, paramétrico e Monte Carlo), o backtesting dos resultados e o stress testing da carteira.

> **Estado:** em desenvolvimento inicial. Já é possível carregar e limpar preços a partir de ficheiros CSV, mas ainda não há funcionalidades de cálculo; o plano completo está no [roadmap](ROADMAP.md).

## O que é o VaR?

O VaR de uma carteira, a um nível de confiança α e num horizonte de *h* dias, é a perda que só é ultrapassada com probabilidade 1 − α. Formalmente, sendo *L* a perda da carteira no horizonte considerado:

$$
\mathrm{VaR}_\alpha(L) = \inf\{\, \ell \in \mathbb{R} : P(L > \ell) \le 1 - \alpha \,\}
$$

Por exemplo, um VaR a 1 dia de 10 000 € com 99 % de confiança significa que, em condições normais de mercado, a perda num dia só deverá exceder 10 000 € em cerca de 1 % dos dias.

O VaR não diz nada sobre a dimensão das perdas nesses piores dias. Para isso usa-se o **Expected Shortfall**, a perda média condicional a ultrapassar o VaR:

$$
\mathrm{ES}_\alpha(L) = \mathbb{E}\left[\, L \mid L \ge \mathrm{VaR}_\alpha(L) \,\right]
$$

Neste projeto, tanto o VaR como o ES são sempre reportados como **perdas positivas** (em percentagem e em euros).

## Instalação

É necessário Python 3.11 ou superior. Recomenda-se instalar o projeto num ambiente virtual:

```bash
git clone https://github.com/Yusa172/Portfolio-Value-at-Risk-Calculator.git
cd Portfolio-Value-at-Risk-Calculator
python -m venv .venv
```

Ativar o ambiente virtual:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Instalar o pacote em modo editável, com as ferramentas de desenvolvimento:

```bash
python -m pip install -e ".[dev]"
```

Para confirmar que a instalação funcionou:

```bash
python -c "import var_calculator; print(var_calculator.__version__)"
```

## Carregar preços

A função `load_prices_csv` lê um ficheiro CSV de preços e devolve um `DataFrame` do pandas indexado por data (ordenado por ordem crescente), com uma coluna por ativo:

```python
from var_calculator.data import load_prices_csv

prices = load_prices_csv("data/sample_prices.csv")
```

São aceites dois formatos, detetados a partir do cabeçalho:

- **largo** — uma coluna de datas e uma coluna de preços por ativo (`Date,ALFA,BETA,...`);
- **longo** — uma linha por par (data, ativo), com as colunas `Date`, `Ticker` e `Price`; as restantes colunas são ignoradas.

Os nomes das colunas podem ser alterados com os argumentos `date_column`, `ticker_column` e `price_column`, e são comparados sem distinguir maiúsculas de minúsculas. A função dá erro (`ValueError`) se faltar uma coluna obrigatória, se houver datas inválidas ou repetidas, ou se algum preço não for numérico. Os preços em falta ficam como `NaN`.

O ficheiro `data/sample_prices.csv` contém preços sintéticos de quatro ativos e pode ser gerado de novo com `python scripts/make_sample_data.py`.

## Limpar preços

Antes de calcular retornos, os preços devem passar por `clean_prices`, que devolve uma tabela em que todos os ativos partilham as mesmas datas:

```python
from var_calculator.data import clean_prices, load_prices_csv

prices = clean_prices(load_prices_csv("data/sample_prices.csv"))
```

A limpeza segue quatro passos, por esta ordem:

1. os preços menores ou iguais a zero (ou infinitos) dão origem a um aviso (`PriceDataWarning`) e passam a ser tratados como valores em falta, porque não são cotações válidas e tornam o retorno logarítmico indefinido;
2. as datas em que nenhum ativo tem preço (por exemplo, um feriado comum a todos os mercados) são removidas;
3. as falhas são preenchidas com o último preço conhecido do mesmo ativo (*forward-fill*), no máximo durante `max_fill` datas seguidas (5 por omissão; `max_fill=0` desativa o preenchimento);
4. as datas em que ainda falte o preço de algum ativo são removidas, ficando apenas a amostra comum a todos (com `drop_incomplete=False` essas falhas ficam como `NaN`).

Repetir o último preço equivale a assumir um retorno nulo nesse dia, o que é razoável para ativos com calendários de negociação diferentes. O limite evita que uma falha longa (um ativo suspenso, por exemplo) seja substituída por uma linha plana, que faria a volatilidade parecer mais baixa do que é. Os valores anteriores à primeira observação de um ativo nunca são preenchidos, para não usar informação do futuro.

## Desenvolvimento

O estilo do código é verificado com o [ruff](https://docs.astral.sh/ruff/), configurado no `pyproject.toml` (regras de estilo, imports ordenados, docstrings no formato NumPy e proibição de `print` no código da biblioteca). Com o ambiente virtual ativo:

```bash
python -m ruff check .            # lint
python -m ruff format --check .   # verificar a formatação
python -m ruff format .           # aplicar a formatação
python -m pytest                  # testes
```

Estas mesmas verificações correm automaticamente no GitHub Actions (`.github/workflows/ci.yml`) em cada *push* e *pull request*, em Python 3.11 e 3.12.

## Roadmap

O desenvolvimento segue um plano de 100 pontos, organizado em dez fases (fundações, retornos e carteira, métodos de VaR, Expected Shortfall, backtesting, stress testing, gráficos, interface, qualidade e versão 1.0). O estado de cada ponto está em [ROADMAP.md](ROADMAP.md).
