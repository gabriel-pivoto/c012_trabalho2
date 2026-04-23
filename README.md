# Simulação Educacional de Escalonamento de CPU

Este projeto foi desenvolvido para a disciplina de Sistemas Operacionais com foco em duas etapas complementares:

- **Parte 1**: comparação entre algoritmos clássicos de escalonamento de CPU;
- **Parte 2**: demonstração de sincronização de threads com recursos compartilhados.

Na parte 1, os algoritmos comparados são:

- `SJF` (`Shortest Job First`)
- `PS` (`Priority Scheduling`)

O cenário textual usa pacientes como analogia para processos, mas a lógica implementada continua sendo a de uma simulação didática de escalonamento de CPU. O comportamento dos algoritmos depende apenas de `arrival_time`, `burst_time` e `priority`.

## Objetivo do trabalho

Comparar como `SJF` e `PS`, ambos na versão **não-preemptiva**, afetam:

- ordem de execução;
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

O `Shortest Job First` escolhe, a cada decisão, o processo pronto com menor tempo de execução (`burst_time`).

Critérios de desempate adotados:

1. menor `arrival_time`;
2. maior `priority`;
3. ordem original de entrada.

### PS

O `Priority Scheduling` escolhe, a cada decisão, o processo pronto com maior prioridade.

Critérios de desempate adotados:

1. menor `arrival_time`;
2. menor `burst_time`;
3. ordem original de entrada.

## Convenção de prioridade adotada

Neste projeto, a convenção é:

- **quanto maior o número, maior a prioridade**

Isso está explícito no código e no relatório para evitar ambiguidade, já que alguns materiais usam a convenção oposta.

## Métricas calculadas

Para cada processo:

- `arrival_time`: instante em que o processo entra na fila de prontos;
- `burst_time`: tempo de CPU necessário;
- `priority`: importância relativa usada pelo `PS`;
- `start_time`: instante em que a execução começa;
- `finish_time`: instante em que a execução termina;
- `waiting_time`: tempo total na fila antes da execução;
- `turnaround_time`: `finish_time - arrival_time`;
- `response_time`: `start_time - arrival_time`.

Como a implementação é não-preemptiva, `waiting_time` e `response_time` coincidem nesta simulação, mas ambos são exibidos separadamente por valor didático.

Também são calculadas as médias de:

- tempo de espera;
- turnaround;
- tempo de resposta.

## CPU ociosa

Quando nenhum processo está pronto no instante atual, a CPU é considerada ociosa e o tempo avança até o próximo `arrival_time`. Isso aparece:

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

Execução com o conjunto padrão:

```bash
python main.py
```

Execução carregando um JSON:

```bash
python main.py --json data/example_processes.json
```

Execução em modo interativo:

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
- tempo de chegada (opcional, com padrão `0`);
- tempo gasto (`burst_time`);
- prioridade.

Executando os testes:

```bash
python -m unittest discover -s tests -v
```

## Formato do JSON opcional

O arquivo JSON deve conter uma lista de objetos:

```json
[
  {
    "id": "P1",
    "name": "Paciente Ana",
    "arrival_time": 0,
    "burst_time": 10,
    "priority": 9,
    "severity_label": "grave",
    "max_wait_tolerated": 2
  }
]
```

Os campos opcionais são apenas narrativos e **não alteram a lógica de scheduling**.

## Conjunto de dados de exemplo

O conjunto padrão foi escolhido para evidenciar o contraste entre:

- favorecer processos curtos, como no `SJF`;
- favorecer processos importantes, como no `PS`.

Ele inclui:

- um processo muito prioritário e longo;
- vários processos curtos;
- tempos de chegada diferentes;
- um trecho com `IDLE` para mostrar CPU ociosa.

## Discussão breve dos resultados

No conjunto padrão:

- o `SJF` tende a reduzir o tempo médio de espera ao priorizar rajadas curtas;
- o `PS` beneficia fortemente processos muito prioritários;
- nem sempre o algoritmo com melhor média é o melhor para todos os processos.

Um processo longo e muito prioritário pode começar imediatamente em `PS`, mas esperar bastante em `SJF`. Em compensação, processos curtos costumam sofrer menos em `SJF`.

## Limitações da simulação

- A implementação é **não-preemptiva**, portanto um processo escolhido mantém a CPU até terminar.
- O projeto não modela troca de contexto, I/O, múltiplos núcleos ou bloqueios.
- `Priority Scheduling` pode sofrer com **starvation**: processos de baixa prioridade podem esperar indefinidamente se chegarem processos mais prioritários com frequência.
- O cenário hospitalar é apenas uma narrativa de apoio; a simulação representa conceitos de escalonamento de processos.

## Possíveis extensões futuras

- versão preemptiva de `SJF` (`SRTF`);
- versão preemptiva de `PS`;
- mecanismo de `aging` no `PS`;
- comparação com `FCFS` e `Round Robin`;
- exportação de resultados para `CSV`.

## Exemplo resumido de saída

```text
SIMULAÇÃO EDUCACIONAL DE ESCALONAMENTO DE CPU
Analogia hospitalar opcional: nomes podem representar pacientes, mas a lógica é de processos.

Entrada original
---------------
ID | Nome          | Chegada | Burst | Prio
---+---------------+---------+-------+-----
P1 | Paciente Ana  |       0 |    10 |    9
P2 | Paciente Bruno|       0 |     2 |    3
...

SJF (não-preemptivo)
--------------------
Ordem de execução: P2 -> P3 -> P5 -> P6 -> P4 -> P1 -> P7
| P2 | P3 | P5 | P6 | P4 | P1 | IDLE | P7 |
0    2    3    6    8    12   22     25   27

PS (não-preemptivo)
-------------------
Ordem de execução: P1 -> P4 -> P6 -> P2 -> P5 -> P3 -> P7
| P1 | P4 | P6 | P2 | P5 | P3 | IDLE | P7 |
0    10   14   16   18   21   22     25   27
```

## Observação final

Este projeto é uma **simulação educacional inspirada nos conceitos de escalonamento de processos da disciplina de Sistemas Operacionais**. O objetivo central é didático: visualizar como diferentes políticas de seleção afetam métricas e percepção de justiça no uso da CPU.
