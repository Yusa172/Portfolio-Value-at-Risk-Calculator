# Portfolio Value-at-Risk Calculator

Biblioteca em Python para medir o risco de mercado de uma carteira de ativos através do **Value-at-Risk (VaR)** e do **Expected Shortfall (ES)**. O objetivo é reunir, num só pacote testado e documentado, os métodos mais usados na prática (histórico, paramétrico e Monte Carlo), o backtesting dos resultados e o stress testing da carteira.

> **Estado:** em desenvolvimento inicial. Ainda não há funcionalidades de cálculo; o plano completo está no [roadmap](ROADMAP.md).

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

## Roadmap

O desenvolvimento segue um plano de 100 pontos, organizado em dez fases (fundações, retornos e carteira, métodos de VaR, Expected Shortfall, backtesting, stress testing, gráficos, interface, qualidade e versão 1.0). O estado de cada ponto está em [ROADMAP.md](ROADMAP.md).
