# Copy Bot Dev Lavmendonca

Bot local de `paper copy trading` para wallets públicas da Polymarket.

O projeto foi feito para testar cópia de wallets sem risco real. Ele acompanha a atividade pública da wallet-fonte, aplica filtros de execução e mantém um painel live com banca fictícia, posições abertas, histórico e marcação a mercado.

## O que ele faz

- `Fixed USDC`
- `Mirror source %`
- filtro de `slippage`
- filtro de `price range`
- limite de `max total`
- limite de `max per market`
- dashboard live em tempo real
- persistência local do estado do paper bot
- marcação a mercado das posições abertas

## Requisitos

- Windows com PowerShell
- Python `3.11+`
- acesso à internet para consultar os endpoints públicos da Polymarket

O projeto usa só biblioteca padrão do Python. Não precisa instalar dependências externas.

## Clonagem

```powershell
git clone https://github.com/LAVMendonca-labs/copy-bot-dev-lavmendonca.git
cd copy-bot-dev-lavmendonca
```

## Estrutura

```text
copy_bot_dev/
  core.py
  live.py
  live_report.py
example_scenario.json
run_copy_bot_dev.py
run_copy_bot_live.py
start-copy-bot-live.ps1
stop-copy-bot-live.ps1
```

## Rodar o simulador local

Esse modo processa um cenário de trades e imprime o estado final em JSON.

```powershell
python .\run_copy_bot_dev.py --copy-name "Weather paper" --wallet 0x...
```

### Exemplo com filtros

```powershell
python .\run_copy_bot_dev.py `
  --copy-name "Teste conservador" `
  --wallet 0x... `
  --mode fixed_usdc `
  --fixed-amount 10 `
  --slippage-pct 3 `
  --price-min-cents 10 `
  --price-max-cents 85 `
  --max-total 100 `
  --max-per-market 20 `
  --bankroll 100
```

### Usar um cenário customizado

```powershell
python .\run_copy_bot_dev.py `
  --scenario .\example_scenario.json `
  --json-out .\state.json
```

## Rodar o painel live

### Jeito simples

```powershell
.\start-copy-bot-live.ps1 -RefreshSeconds 20 -Port 8875
```

Depois abra:

- `http://127.0.0.1:8875/`
- `http://127.0.0.1:8875/api/state`

### Jeito direto pelo Python

```powershell
python .\run_copy_bot_live.py `
  --host 127.0.0.1 `
  --port 8875 `
  --refresh-seconds 20 `
  --activity-limit 200 `
  --positions-limit 200
```

### Parar o painel

```powershell
.\stop-copy-bot-live.ps1
```

## Como usar no painel

1. Clique em `New copy`.
2. Preencha:
   - `Copy name`
   - `Wallet to follow`
   - `Mode`
   - `Fixed amount` ou `Mirror source %`
   - `Slippage`
   - `Price range`
   - `Max total`
   - `Max per market`
   - `Bankroll`
   - `Min trade`
3. Salve.
4. O acompanhamento começa dali para frente. O bot não deve copiar o backlog antigo da wallet recém-cadastrada.

## Como preencher cada campo

### Copy name

Nome interno da configuração.

Use algo que identifique rapidamente a estratégia ou a forma de acompanhamento.

Exemplos:

- `Weather teste 01`
- `Política conservador`
- `Crypto agressivo`

### Wallet to follow

Endereço público da wallet que será seguida.

Formato:

```text
0x...
```

Se a wallet estiver errada, o copy não vai acompanhar nada útil.

### Mode

Define como o tamanho das entradas será calculado.

#### Fixed USDC

Cada entrada tenta copiar um valor fixo em dólar.

Exemplo:

- `10` = tenta copiar `10 USDC` por entrada

É o modo mais previsível para testar.

#### Mirror source %

O tamanho da entrada tenta acompanhar proporcionalmente a ordem da wallet-fonte.

Exemplo:

- `100` = tenta espelhar `100%` do tamanho relativo permitido pelos seus limites

É mais fiel à wallet, mas também mais agressivo.

### Fixed amount (USDC)

Aparece quando o modo é `Fixed USDC`.

Sugestão de uso:

- conservador: `2`, `5`, `10`
- médio: `10`, `20`
- agressivo: `25+`

### Mirror source %

Aparece quando o modo é `Mirror source %`.

Sugestão de uso:

- conservador: `10` a `25`
- médio: `25` a `50`
- agressivo: `75` a `100`

### Slippage (%)

Tolerância máxima entre o preço da wallet-fonte e o preço atual do mercado no momento da cópia.

Quanto maior:

- mais execuções entram
- pior tende a ficar o preço

Quanto menor:

- mais proteção de preço
- mais sinais são rejeitados

Sugestão:

- conservador: `1` a `2`
- equilibrado: `2` a `3`
- agressivo: `4` a `5`

### Price range (cents)

Faixa de preço permitida para copiar.

Exemplos:

- `0` até `100`: copia qualquer preço
- `10` até `85`: evita extremos
- `15` até `80`: mais seletivo

Isso ajuda a evitar copiar odds muito comprimidas perto de `0c` ou `100c`.

### Max total (USDC)

Exposição máxima total da configuração.

É a soma de todas as posições abertas daquele copy.

Exemplo:

- `100` = o copy pode ter até `100 USDC` abertos no total

### Max per market (USDC)

Exposição máxima permitida em um único mercado.

Exemplo:

- `20` = o copy nunca deve passar de `20 USDC` naquele evento específico

Isso evita concentração excessiva.

### Bankroll (USDC)

Banca fictícia inicial do paper bot.

É o capital base usado para calcular caixa, exposição e PnL.

Exemplo:

- `100`
- `500`
- `1000`

### Min trade (USDC)

Valor mínimo aceitável para uma execução paper.

Se o trade calculado ficar abaixo desse valor depois dos limites e truncamentos, o bot rejeita a entrada.

Sugestão:

- `1` para testes simples
- `0.5` se quiser simular entradas menores

## Persistência

O estado do bot live fica salvo em:

```text
reports/copy_live_state.json
```

Isso permite reiniciar o processo sem perder as posições paper e as configurações cadastradas.

## Observações

- É um projeto de `paper trading`, não de execução real.
- Wallets muito estruturais podem quase não emitir `SELL` explícito. Nesses casos, o bot também observa a redução da posição pública da wallet-fonte.
- O valor atual das posições abertas é marcado a mercado com base no `order book` mais recente.

## Publicação e contribuição

Se quiser evoluir o projeto:

```powershell
git checkout -b minha-feature
git add .
git commit -m "Minha melhoria"
git push origin minha-feature
```
