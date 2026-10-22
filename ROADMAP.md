# Roadmap

Plano de desenvolvimento do Portfolio Value-at-Risk Calculator em 100 pontos. Cada ponto é uma entrega pequena e testada; os pontos estão por ordem e cada um pode depender dos anteriores.

## Fase 1 — Fundações

- [ ] **1. Estrutura do projeto** — `pyproject.toml` (layout `src/`, pacote `var_calculator`, Python ≥ 3.11, extra `dev`), `.gitignore` para Python e `src/var_calculator/__init__.py` com `__version__`.
- [ ] **2. README inicial** — o que é o projeto, o que é o VaR em poucas linhas, instalação com ambiente virtual e link para este roadmap.
- [ ] **3. Testes** — pytest configurado no `pyproject.toml` e um primeiro teste que importa o pacote.
- [ ] **4. Lint e formatação** — ruff (lint e format) configurado e aplicado a todo o código.
- [ ] **5. CI** — GitHub Actions a correr ruff e pytest em Python 3.11 e 3.12 em cada push.
- [ ] **6. Dados de exemplo** — `scripts/make_sample_data.py` gera preços sintéticos reprodutíveis (seed fixa) para 4 ativos em `data/sample_prices.csv`.
- [ ] **7. Carregar preços** — `data.load_prices_csv()` lê CSV em formato largo ou longo e devolve um DataFrame indexado por data, com validação de colunas.
- [ ] **8. Limpeza de dados** — alinhar datas entre ativos, forward-fill limitado, remover linhas vazias e avisar sobre preços ≤ 0.
- [ ] **9. Download de preços** — `data.download_prices()` com yfinance (dependência opcional) e cache local em `data/cache/` (ignorado no git).
- [ ] **10. Testes de dados** — leitura, limpeza e erros; o download é testado com mock, sem rede.

## Fase 2 — Retornos e portfólio

- [ ] **11. Retornos** — retornos simples e logarítmicos em `returns.py`.
- [ ] **12. Classe `Portfolio`** — dataclass com tickers, pesos e valor investido; valida que os pesos somam 1 e que os tickers existem nos dados.
- [ ] **13. Pesos e posições** — converter pesos em montantes e quantidades, e o inverso.
- [ ] **14. Retornos do portfólio** — série de retornos e de P&L em euros a partir dos pesos.
- [ ] **15. Estatísticas descritivas** — média, desvio-padrão, assimetria, curtose, mínimo e máximo por ativo e do portfólio.
- [ ] **16. Covariância e correlação** — matrizes amostrais.
- [ ] **17. Covariância EWMA** — modelo RiskMetrics com λ = 0,94 configurável.
- [ ] **18. Escala temporal** — regra da raiz do tempo para horizontes de h dias, com nota sobre as suas limitações.
- [ ] **19. Testes** — retornos, portfólio e covariâncias comparados com valores calculados à mão.
- [ ] **20. Exemplo** — `examples/01_portfolio_basics.py`.

## Fase 3 — Métodos de VaR

- [ ] **21. Resultado comum** — `VaRResult` com valor em % e em €, nível de confiança, horizonte e método; a perda é sempre um número positivo.
- [ ] **22. VaR histórico** — percentil empírico das perdas.
- [ ] **23. Janela configurável** — VaR histórico com janela móvel (ex.: 250 ou 500 dias).
- [ ] **24. VaR histórico ponderado por idade** — método de Boudoukh, Richardson e Whitelaw.
- [ ] **25. VaR paramétrico normal** — método da variância-covariância para o portfólio.
- [ ] **26. VaR paramétrico t de Student** — graus de liberdade estimados por máxima verosimilhança.
- [ ] **27. VaR Cornish-Fisher** — ajuste à assimetria e à curtose.
- [ ] **28. VaR EWMA** — VaR paramétrico com a volatilidade RiskMetrics.
- [ ] **29. VaR GARCH(1,1)** — com o pacote `arch` como dependência opcional.
- [ ] **30. Monte Carlo normal** — simulação normal multivariada (Cholesky) com seed reprodutível.
- [ ] **31. Monte Carlo t** — simulação t multivariada.
- [ ] **32. Monte Carlo bootstrap** — reamostragem dos retornos históricos.
- [ ] **33. Horizonte multi-dia** — raiz do tempo vs. simulação de caminhos no Monte Carlo.
- [ ] **34. `compute_var(method=...)`** — uma função única que chama qualquer método.
- [ ] **35. Testes dos métodos** — cada método comparado com valores teóricos conhecidos (ex.: normal com μ e σ conhecidos).

## Fase 4 — Expected Shortfall e decomposição do risco

- [ ] **36. ES histórico** — média das perdas para lá do VaR.
- [ ] **37. ES paramétrico** — fórmulas fechadas para a normal e a t de Student.
- [ ] **38. ES Monte Carlo** — a partir das simulações dos pontos 30 a 32.
- [ ] **39. VaR marginal** — sensibilidade do VaR ao peso de cada ativo.
- [ ] **40. VaR por componente** — decomposição de Euler; a soma das componentes é igual ao VaR total.
- [ ] **41. VaR incremental** — efeito de adicionar ou retirar uma posição.
- [ ] **42. Contribuição para o risco** — percentagem do VaR explicada por cada ativo.
- [ ] **43. Benefício da diversificação** — soma dos VaR individuais vs. VaR do portfólio.
- [ ] **44. Testes** — ES e decomposição do risco.
- [ ] **45. Exemplo** — `examples/02_var_methods.py` com todos os métodos lado a lado.

## Fase 5 — Backtesting

- [ ] **46. VaR rolante** — série de VaR out-of-sample, sem look-ahead.
- [ ] **47. Exceções** — contagem e datas dos dias em que a perda ultrapassou o VaR.
- [ ] **48. Teste de Kupiec** — proporção de falhas (POF).
- [ ] **49. Teste de Christoffersen** — independência das exceções.
- [ ] **50. Cobertura condicional** — teste conjunto de Kupiec e Christoffersen.
- [ ] **51. Semáforo de Basileia** — zonas verde, amarela e vermelha.
- [ ] **52. Backtest do ES** — teste Z2 de Acerbi e Székely.
- [ ] **53. Quantile loss** — função de perda para ordenar os métodos.
- [ ] **54. Comparação de métodos** — tabela com exceções, p-valores e perda por método.
- [ ] **55. Relatório de backtest** — exportação para CSV.
- [ ] **56. Testes** — séries sintéticas com resultado conhecido.
- [ ] **57. Exemplo** — `examples/03_backtest.py`.
- [ ] **58. Documentação** — `docs/backtesting.md` com hipóteses, estatísticas e interpretação.

## Fase 6 — Stress testing

- [ ] **59. Cenários históricos** — aplicar ao portfólio atual os retornos de crises (2008, março de 2020, 2022).
- [ ] **60. Cenários hipotéticos** — choques definidos pelo utilizador para cada ativo.
- [ ] **61. Stress de correlação** — VaR com correlações forçadas para perto de 1.
- [ ] **62. Stress de volatilidade** — multiplicador sobre a volatilidade.
- [ ] **63. Reverse stress test** — choque mínimo que provoca uma perda de X €.
- [ ] **64. Relatório de stress** — tabela de perdas por cenário.
- [ ] **65. Testes** — cenários e relatório de stress.
- [ ] **66. Documentação** — `docs/stress_testing.md`.

## Fase 7 — Gráficos

- [ ] **67. Distribuição** — histograma dos retornos com linhas de VaR e ES.
- [ ] **68. P&L e VaR** — P&L diário com o VaR rolante e as exceções assinaladas.
- [ ] **69. Comparação de métodos** — gráfico de barras com o VaR de cada método.
- [ ] **70. Contribuição de risco** — gráfico por ativo.
- [ ] **71. Correlação** — heatmap da matriz de correlação.
- [ ] **72. Sensibilidade** — VaR em função do nível de confiança e do horizonte.
- [ ] **73. Tema visual** — estilo comum a todos os gráficos.
- [ ] **74. Testes de gráficos** — cada gráfico gera um ficheiro sem erros.

## Fase 8 — Interface

- [ ] **75. Configuração** — portfólio definido num ficheiro YAML com validação.
- [ ] **76. CLI** — comando `var-calc` que calcula o VaR a partir do ficheiro de configuração.
- [ ] **77. CLI backtest** — subcomando `backtest`.
- [ ] **78. CLI stress** — subcomando `stress`.
- [ ] **79. Relatório** — relatório em Markdown/HTML com tabelas e gráficos.
- [ ] **80. Excel** — exportação dos resultados para Excel.
- [ ] **81. App Streamlit: portfólio** — escolher ativos, pesos e valor investido.
- [ ] **82. App: parâmetros** — escolher método, nível de confiança e horizonte.
- [ ] **83. App: resultados** — gráficos e tabelas.
- [ ] **84. App: backtesting e stress** — separadores próprios.
- [ ] **85. App: relatório** — botão para descarregar o relatório.
- [ ] **86. Deploy** — instruções para publicar no Streamlit Community Cloud.

## Fase 9 — Qualidade

- [ ] **87. Tipos** — type hints completos e mypy no CI.
- [ ] **88. Cobertura** — pytest-cov com um mínimo definido no CI.
- [ ] **89. Testes de propriedades** — hypothesis (ex.: o VaR cresce com o nível de confiança).
- [ ] **90. Erros claros** — exceções próprias para pesos inválidos, dados insuficientes, etc.
- [ ] **91. Logging** — mensagens configuráveis em vez de `print`.
- [ ] **92. Performance** — vetorizar o Monte Carlo e medir tempos.
- [ ] **93. Multi-moeda** — converter para euros os ativos noutras moedas.
- [ ] **94. pre-commit** — ruff e verificações básicas antes de cada commit.

## Fase 10 — Documentação e versão 1.0

- [ ] **95. Metodologia** — `docs/metodologia.md` com as fórmulas de todos os métodos.
- [ ] **96. Caso de estudo** — portfólio exemplo com resultados e interpretação económica.
- [ ] **97. Notebook** — tutorial completo do início ao fim.
- [ ] **98. README final** — badges, exemplos de uso e imagens.
- [ ] **99. Versão 1.0.0** — `CHANGELOG.md` e tag `v1.0.0`.
- [ ] **100. Revisão final** — limpar o código, rever a documentação e confirmar que tudo corre num ambiente novo.
