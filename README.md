# Copy Bot Dev Lavmendonca

Bot local de `paper copy trading` para wallets públicas da Polymarket.

Este projeto é para **teste**. Ele **não usa dinheiro real**. A ideia é simples: você coloca uma wallet pública da Polymarket, o bot acompanha as entradas dela e simula a cópia com uma banca fictícia.

## Antes de tudo

Você **não precisa**:

- instalar Visual Studio
- saber programar
- criar conta de desenvolvedor

Você só precisa:

- de um computador com Windows
- de internet
- do Python instalado

## O que esse bot faz

- acompanha a atividade pública de uma wallet
- copia em modo de teste (`paper trading`)
- deixa configurar:
  - `Fixed USDC`
  - `Mirror source %`
  - `slippage`
  - `price range`
  - `max total`
  - `max per market`
  - `bankroll`
- mostra painel live em tempo real
- salva o estado localmente para continuar depois

## O que esse bot NÃO faz

- não envia ordem real
- não conecta na MetaMask
- não movimenta seu saldo real
- não garante lucro

## Jeito mais fácil de usar

### 1. Instale o Python

Baixe e instale o Python por aqui:

https://www.python.org/downloads/windows/

Durante a instalação, marque a opção:

`Add Python to PATH`

Se não marcar isso, o comando `python` pode não funcionar no PowerShell.

### 2. Baixe o projeto

Você tem 2 opções.

#### Opção A: baixar ZIP

1. Abra esta página:
   `https://github.com/LAVMendonca-labs/copy-bot-dev-lavmendonca`
2. Clique no botão verde `Code`
3. Clique em `Download ZIP`
4. Extraia o ZIP para uma pasta simples, por exemplo:

```text
C:\copy-bot-dev-lavmendonca
```

#### Opção B: clonar com Git

Se você já usa Git:

```powershell
git clone https://github.com/LAVMendonca-labs/copy-bot-dev-lavmendonca.git
cd copy-bot-dev-lavmendonca
```

## Como abrir o projeto

1. Abra a pasta do projeto
2. Clique na barra de endereço da pasta
3. Digite:

```text
powershell
```

4. Aperte `Enter`

Isso já abre o PowerShell dentro da pasta certa.

## Como rodar o painel live

Esse é o modo principal para quase todo mundo.

No PowerShell, rode:

```powershell
.\start-copy-bot-live.ps1 -RefreshSeconds 20 -Port 8875
```

Depois abra no navegador:

- `http://127.0.0.1:8875/`
- `http://127.0.0.1:8875/api/state`

## Como parar o painel

No PowerShell:

```powershell
.\stop-copy-bot-live.ps1
```

## Se o PowerShell bloquear o `.ps1`

Use o comando direto em Python:

```powershell
python .\run_copy_bot_live.py --host 127.0.0.1 --port 8875 --refresh-seconds 20 --activity-limit 200 --positions-limit 200
```

## O que esperar quando abrir o painel

Você vai ver:

- um resumo geral
- uma lista de copies cadastrados
- um botão `New copy`
- abas de:
  - `History`
  - `Positions`
  - `Source events`

## Como cadastrar um copy

1. Clique em `New copy`
2. Preencha os campos
3. Clique em `Add`

Importante:

- o bot começa a acompanhar **daquele momento para frente**
- ele **não deveria copiar o histórico antigo** da wallet recém-cadastrada

## Como preencher cada campo

### Copy name

É só o nome interno da sua configuração.

Use algo simples para identificar o copy.

Exemplos:

- `Weather teste 01`
- `Política conservador`
- `Crypto agressivo`

### Wallet to follow

É o endereço público da wallet que será seguida.

Formato:

```text
0x...
```

Se a wallet estiver errada, o bot vai seguir a carteira errada.

### Mode

Define como o valor das entradas será calculado.

#### Fixed USDC

Cada entrada tenta copiar um valor fixo.

Exemplo:

- `10` = tenta copiar `10 USDC` por entrada

Esse é o melhor modo para testar com segurança.

#### Mirror source %

O bot tenta copiar proporcionalmente ao tamanho da ordem da wallet-fonte.

Exemplo:

- `100` = tenta espelhar `100%` do tamanho relativo, respeitando seus limites

Esse modo é mais fiel à wallet, mas também mais agressivo.

### Fixed amount (USDC)

Aparece quando o modo é `Fixed USDC`.

Sugestão:

- conservador: `2`, `5`, `10`
- médio: `10`, `20`
- agressivo: `25+`

### Mirror source %

Aparece quando o modo é `Mirror source %`.

Sugestão:

- conservador: `10` a `25`
- médio: `25` a `50`
- agressivo: `75` a `100`

### Slippage (%)

É a tolerância máxima entre o preço da wallet-fonte e o preço atual do mercado.

Quanto maior:

- mais sinais entram
- pior tende a ser o preço de entrada

Quanto menor:

- mais proteção
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

### Max total (USDC)

Exposição máxima total desse copy.

É a soma de todas as posições abertas daquela configuração.

Exemplo:

- `100` = o copy pode deixar até `100 USDC` abertos no total

### Max per market (USDC)

Exposição máxima permitida em um único mercado.

Exemplo:

- `20` = o copy nunca deve passar de `20 USDC` em um evento específico

### Bankroll (USDC)

Banca fictícia inicial do paper bot.

Exemplos:

- `100`
- `500`
- `1000`

### Min trade (USDC)

Valor mínimo aceitável para uma execução paper.

Se o valor final da entrada ficar abaixo disso, o bot rejeita o sinal.

Sugestão:

- `1` para a maioria dos testes
- `0.5` se quiser simular entradas menores

## Como interpretar o painel

### History

Mostra o histórico processado do copy.

### Positions

Mostra as posições abertas do paper bot.

Importante:

- uma posição pode juntar várias entradas no mesmo mercado
- `Traded` = custo acumulado naquela perna
- `Value` = valor atual marcado a mercado
- `AVG -> NOW` = preço médio de entrada comparado com a cotação atual

### Source events

Mostra os eventos mais recentes detectados na wallet-fonte.

## Se eu desligar a tela, ele continua?

Se o computador continuar ligado e o processo continuar rodando, sim.

Se o computador dormir, reiniciar ou o processo fechar, não.

O projeto salva o estado em:

```text
reports/copy_live_state.json
```

E agora também grava um log contínuo em:

```text
reports/copy_live_heartbeat.jsonl
```

Esse arquivo ajuda a verificar depois se o bot realmente ficou rodando.

## Erros comuns

### `python` não é reconhecido

Significa que o Python não foi instalado corretamente no `PATH`.

Solução:

1. reinstale o Python
2. marque `Add Python to PATH`

### `ERR_CONNECTION_REFUSED`

Significa que o painel não está rodando.

Solução:

1. volte para a pasta do projeto
2. rode:

```powershell
.\start-copy-bot-live.ps1 -RefreshSeconds 20 -Port 8875
```

### O PowerShell bloqueou o script

Use o comando direto:

```powershell
python .\run_copy_bot_live.py --host 127.0.0.1 --port 8875 --refresh-seconds 20 --activity-limit 200 --positions-limit 200
```

### O painel abriu, mas não aparece nada

Verifique:

- se a wallet foi cadastrada corretamente
- se a wallet está operando de verdade
- se você salvou o copy
- se o bot começou a acompanhar só a partir do momento do cadastro

## Rodar o simulador simples

Esse modo é opcional. Serve para testar um cenário em JSON.

```powershell
python .\run_copy_bot_dev.py --copy-name "Teste local" --wallet 0x...
```

Ou com cenário customizado:

```powershell
python .\run_copy_bot_dev.py --scenario .\example_scenario.json --json-out .\state.json
```

## Arquivos principais

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

## Aviso final

Este projeto é para **simulação**.

Ele foi feito para:

- estudar wallets
- testar filtros
- entender copy trading
- validar comportamento com banca fictícia

Não foi feito para prometer lucro nem para substituir gestão de risco.
