# Simulacao Educacional de Escalonamento de CPU

Este projeto foi desenvolvido para a disciplina de Sistemas Operacionais com foco em duas etapas complementares:

- **Parte 1**: comparação entre algoritmos clássicos de escalonamento de CPU;
- **Parte 2**: demonstração de sincronização de threads com recursos compartilhados.

Na parte 1, os algoritmos comparados são:

- `SJF` (`Shortest Job First`)
- `PS` adaptado para um cenario hospitalar com atendimento por menor tempo de vida

O cenario textual usa pacientes como analogia para processos, mas a logica continua sendo a de uma simulacao educacional inspirada em escalonamento de CPU.

## Objetivo do trabalho

Comparar como `SJF` e o algoritmo por menor tempo de vida, ambos na versao nao-preemptiva, afetam:

- ordem de execucao;
- tempo de espera;
- turnaround;
- tempo de resposta;
- percepção de justiça entre processos curtos, longos e prioritários.

Além disso, usar a fila gerada na parte 1 como entrada da parte 2 para demonstrar:

- corrida critica sem sincronização;
- proteção por `threading.Lock`;
- consistência final de estoque e prontuário compartilhados.

## Algoritmos implementados

### SJF

O `Shortest Job First` escolhe, a cada decisao, o paciente pronto e vivo com menor `burst_time`.

Criterios de desempate adotados:

1. menor `arrival_time`;
2. menor tempo de vida atual;
3. ordem original de entrada.

### PS adaptado para menor tempo de vida

O segundo algoritmo ocupa o lugar do antigo `Priority Scheduling`, mas agora foi reinterpretado para o cenario hospitalar.

Nesta adaptacao:

- o antigo campo de prioridade foi substituido por `life_time`;
- menor tempo de vida significa urgencia maior;
- o paciente mais proximo de morrer deve ser atendido primeiro.

Criterios de desempate adotados:

1. menor `arrival_time`;
2. menor `burst_time`;
3. ordem original de entrada.

Importante: esta mecanica nao representa o `Priority Scheduling` classico da teoria. Trata-se de uma adaptacao didatica para o cenario hospitalar.

## Regra de tempo de vida

Cada paciente entra no sistema com um tempo de vida inicial.

Durante a simulacao:

- pacientes aguardando perdem tempo de vida com a passagem do tempo;
- pacientes que ainda nao chegaram nao perdem tempo de vida antes do `arrival_time`;
- o paciente que esta em atendimento nao perde tempo de vida durante a propria consulta;
- se o tempo de vida chegar a `0`, o paciente nao resiste e sai da simulacao;
- pacientes mortos nao sao escalonados depois.

## Metricas calculadas

Para cada paciente:

- `arrival_time`
- `burst_time`
- `life_time` inicial
- `life_time` final
- `start_time`
- `finish_time`
- `waiting_time`
- `turnaround_time`
- `response_time`
- `status_final`
- `death_time`, quando houver

Tambem sao calculadas, por algoritmo:

- tempo medio de espera entre os pacientes atendidos;
- tempo medio de turnaround entre os pacientes atendidos;
- tempo medio de resposta entre os pacientes atendidos;
- quantidade de pacientes que resistiram;
- quantidade de pacientes que nao resistiram.

## CPU ociosa

Quando nenhum paciente vivo esta pronto no instante atual, a CPU fica ociosa ate o proximo `arrival_time`.

Isso aparece:

- na linha do tempo do algoritmo;
- no gráfico de Gantt textual, por meio do bloco `IDLE`.

## Parte 2: Sincronização de Threads

A parte 2 simula vários médicos (threads) consumindo uma fila única de pacientes produzida a partir de um dos algoritmos da parte 1 (`SJF` ou `PS`).

Recursos compartilhados simulados:

- prontuário (lista de registros finais);
- estoque de medicação.

Dois cenários são executados no mesmo relatório:

- **sem sincronização**: leitura/checagem/decremento/registro sem lock;
- **com sincronização**: seção crítica protegida com `threading.Lock`.

Para cada atendimento, o relatório mostra em terminal:

- médico;
- paciente;
- quantidade solicitada;
- estoque antes e depois;
- status (`ATENDIDO` ou `SEM_RECURSO`).

No final de cada cenário, é exibido um resumo com verificação automática de consistência.

## Estrutura do projeto

```text
project/
  main.py
  models.py
  schedulers.py
  thread_sync.py
  metrics.py
  gantt.py
  sample_data.py
  cli.py
  README.md
  data/
    example_processes.json
  tests/
    test_sjf.py
    test_ps.py
    test_metrics.py
    test_thread_sync.py
```

## Como executar

Requisitos:

- Python `3.11+`

Execucao com o conjunto padrao:

```bash
python main.py
```

Execucao carregando um JSON:

```bash
python main.py --json data/example_processes.json
```

Execucao em modo interativo:

```bash
python main.py --interactive
```

Configurações da parte 2 (opcionais):

```bash
python main.py --sync-doctors 4 --sync-queue-source ps --sync-stock 12 --sync-seed 123
```

Parâmetros:

- `--sync-doctors`: quantidade de médicos (threads) da parte 2;
- `--sync-queue-source`: escolhe se a fila vem de `sjf` ou `ps`;
- `--sync-stock`: estoque inicial (se omitido, é calculado automaticamente);
- `--sync-seed`: seed opcional para reproduzir as requisições.

No modo interativo, a CLI pede:

- nome da pessoa/processo;
- tempo de chegada, opcional, com padrao `0`;
- tempo gasto (`burst_time`);
- tempo de vida inicial.

Executando os testes:

```bash
python -m unittest discover -s tests -v
```

## Formato do JSON opcional

O arquivo JSON pode usar `life_time` como campo principal. Tambem ha compatibilidade com `tempo_de_vida` e com o campo antigo `priority`.

Exemplo:

```json
[
  {
    "id": "P1",
    "name": "Paciente Ana",
    "arrival_time": 0,
    "burst_time": 3,
    "life_time": 2,
    "severity_label": "grave",
    "max_wait_tolerated": 2
  }
]
```

Os campos opcionais sao apenas narrativos e nao alteram a logica do escalonamento.

## Conjunto de dados de exemplo

O conjunto padrao foi ajustado para evidenciar a nova regra:

- um paciente com burst curto e vida alta;
- um paciente com burst mais longo e vida muito baixa;
- situacoes em que o `SJF` reduz a espera media;
- situacoes em que o algoritmo por menor tempo de vida preserva mais pacientes vivos.

## Discussao breve dos resultados

No conjunto padrao:

- o `SJF` tende a reduzir o tempo medio de espera ao priorizar consultas curtas;
- o algoritmo por menor tempo de vida tende a salvar pacientes mais urgentes;
- menor espera media nem sempre significa melhor resultado de sobrevivencia.

Esse contraste ajuda a visualizar o conflito entre eficiencia media e urgencia clinica no cenario adaptado.

## Limitacoes da simulacao

- A implementacao e nao-preemptiva.
- O projeto nao modela troca de contexto, I/O, multiplos nucleos ou bloqueios.
- A regra de tempo de vida e uma adaptacao didatica do problema.
- O antigo `PS` foi reinterpretado para o cenario hospitalar e nao corresponde ao algoritmo teorico classico.

## Possiveis extensoes futuras

- versao preemptiva de `SJF` (`SRTF`);
- mecanismo de `aging`;
- comparacao com `FCFS` e `Round Robin`;
- exportacao de resultados para `CSV`.

## Exemplo resumido de saida

```text
SIMULACAO EDUCACIONAL DE ESCALONAMENTO DE CPU
Analogia hospitalar opcional: nomes podem representar pacientes, mas a logica e de processos.
Menor tempo de vida = maior urgencia; pacientes aguardando perdem vida com a passagem do tempo.

Entrada original
----------------
ID | Nome            | Chegada | Burst | Vida
---+-----------------+---------+-------+-----
P1 | Paciente Ana    |       0 |     3 |    2
P2 | Paciente Bruno  |       0 |     3 |    5
...

SJF (nao-preemptivo)
--------------------
Ordem de execucao: P3 -> P4 -> P2 -> P5

PS adaptado (menor tempo de vida)
---------------------------------
Ordem de execucao: P1 -> P2 -> P3 -> P4 -> P5
```

## Observacao final

Este projeto continua sendo uma simulacao educacional inspirada nos conceitos de escalonamento de processos da disciplina de Sistemas Operacionais, com uma adaptacao hospitalar baseada em tempo de vida para tornar o comportamento dos algoritmos mais intuitivo no relatorio final.
