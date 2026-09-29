# Testes de Integração: Agendamento de Voos de Helicóptero

Projeto acadêmico de testes de integração da AeroLog Helicópteros. A aplicação integra serviço, validação operacional e persistência SQLite sem camada HTTP.

## Requisitos

- Python 3.10 ou superior
- pip

## Instalação e execução

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest -v
```

Para executar os testes com cobertura:

```powershell
pytest --cov=src --cov-report=term-missing
```

Para gerar novamente o relatório PDF após instalar as dependências:

```powershell
python tools/generate_report.py
```

O comando executa novamente os testes e atualiza `docs/relatorio_tecnico.pdf` e a transcrição integral em `docs/evidencias/execucao_pytest.txt`. A transcrição é saída textual real do terminal, não captura de tela; para atender literalmente ao item de screenshots da atividade, inclua capturas próprias da execução de `pytest -v` e da cobertura.

## Arquitetura

`BookingService` abre uma transação SQLite com `BEGIN IMMEDIATE`, consulta a aeronave, delega elegibilidade a `FlightValidator`, consulta conflitos de intervalo e somente então insere o voo como `AGENDADO`. Qualquer exceção provoca rollback. Os horários são convertidos para UTC; intervalos adjacentes são permitidos e intervalos sobrepostos são recusados.

## Cenários cobertos

- Agendamento válido e consulta do registro persistido.
- Conflito entre intervalos sobrepostos sem inserir o segundo voo.
- Aeronave em inspeção recusada sem gravação.
- Banco temporário por teste, garantindo isolamento das fixtures.
- Peso acima da capacidade útil recusado sem gravação.

## Estrutura

```text
src/       módulos de banco, validação e serviço
tests/     fixtures e testes de integração
docs/      relatório técnico em PDF e fontes
tools/     gerador do PDF
```

O banco utilizado pelos testes é criado em diretório temporário do pytest e removido ao final. Nenhum servidor ou API externa é necessário.

## Publicação no GitHub

O diretório pode ser publicado criando um repositório público vazio no GitHub e configurando o remoto fornecido pela sua conta:

```powershell
git remote add origin <URL-DO-REPOSITORIO>
git add .
git commit -m "Implementa testes de integração de voos"
git push -u origin main
```

O push exige uma conta GitHub autenticada e um remoto válido.