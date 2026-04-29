# Apresentação: Escalonamento de CPU - Hospital

## Resumo Executivo
Simulador que compara 2 algoritmos de escalonamento usando analogia de hospital:
- **SJF** (Shortest Job First): Menor duração primeiro
- **PS** (Priority): Menor tempo de vida (urgência) primeiro

**Tempo total**: 15-20 minutos

---

## Estrutura da Apresentação

### 1. Introdução (2 min)
- O que é escalonamento de CPU?
- Por que importa?
- Analogia: Pacientes (processos), Médicos (CPU), Medicamentos (recursos)

### 2. Algoritmo SJF (2 min)
**Como funciona**: Escolhe o paciente com menor tempo de atendimento
```
Dados: P1(3 min), P2(3 min), P3(1 min), P4(1 min), P5(1 min)
Ordem: P3 → P4 → P1 → P2 → P5
Resultado: 4 atendidos, 4 vivos (ANA MORRE - burst curto não significa urgência)
Tempo médio espera: 0.50
```

### 3. Algoritmo PS (2 min)
**Como funciona**: Escolhe o paciente com menor tempo de vida (mais urgente)
```
Dados: P1(life=2), P2(life=5), P3(life=9), P4(life=8), P5(life=4)
Ordem: P1 → P2 → P3 → P4 → P5
Resultado: 5 atendidos, 5 vivos (TODOS SALVOS - urgentes prioritários)
Tempo médio espera: 3.00
```

### 4. Comparação (1 min)
- **SJF**: Melhor eficiência (tempo médio menor)
- **PS**: Melhor humanitário (salva urgentes)
- Escolha depende do objetivo

### 5. Demo GUI (8 min)
1. Abrir GUI: `python gui.py`
2. Aba Dados: Carregar dados padrão
3. Aba Simulação: Executar
   - Mostrar SJF: Gantt + Tabela (note Ana faltando)
   - Mostrar PS: Gantt + Tabela (todos presentes)
4. Aba Comparação: Análise automática
5. Aba Sincronização: Teste com threads

### 6. Sincronização (3 min)
**Problema**: Múltiplos médicos (threads) compartilham estoque
```
Sem Lock:
  Thread 1: stock=10 → lê → tira 5 → stock=5
  Thread 2: stock=10 → lê → tira 3 → stock=7 ❌ ERRADO

Com Lock:
  Thread 1: LOCK → stock=10 → tira 5 → stock=5 → UNLOCK
  Thread 2: ESPERA → LOCK → stock=5 → tira 3 → stock=2 → UNLOCK ✓ CERTO
```
Lock garante atomicidade, evita race condition.

### 7. Conclusão (1 min)
- Não existe algoritmo "melhor", apenas "melhor para o caso"
- Sincronização é essencial
- Perguntas?

---

## Dados Padrão (5 Pacientes)

| ID | Nome | Chegada | Duração | Vida | Severidade |
|----|------|---------|---------|------|-----------|
| P1 | Ana | 0 | 3 | 2 | GRAVE |
| P2 | Bruno | 0 | 3 | 5 | GRAVE |
| P3 | Carla | 0 | 1 | 9 | LEVE |
| P4 | Daniel | 1 | 1 | 8 | MODERADO |
| P5 | Elisa | 10 | 1 | 4 | MODERADO |

---

## Métricas Chave

**waiting_time** = start_time - arrival_time (quanto esperou)
**turnaround** = finish_time - arrival_time (tempo total no sistema)
**response_time** = start_time - arrival_time (até começar atendimento)
**status** = RESISTIU ou NÃO RESISTIU

### Exemplo: P1 (Ana) em SJF
- Chegou: t=0
- Começou: t=6 (após P3, P4, P2)
- Terminou: Nunca (morreu esperando)
- waiting_time = 6 - 0 = 6
- Status = NÃO RESISTIU (vida=2, esperou 2+ unidades)

---

## Respostas Rápidas

**P: Por que Ana morreu em SJF mas não em PS?**
→ SJF atende Carla (1 min) antes de Ana. Ana morre esperando. PS atende Ana primeira (urgência=2 min de vida), salva ela.

**P: Qual algoritmo é melhor?**
→ Depende: SJF minimiza tempo médio. PS salva urgências. Real OS usa combinações.

**P: Por que usar Lock?**
→ Sem Lock, 2 threads leem o mesmo estoque e ambas "pegam", causando inconsistência. Lock evita.

**P: Como validar os tempos?**
→ Check: turnaround = finish - arrival ✓ | waiting = start - arrival ✓

**P: E se adicionar mais pacientes?**
→ Tendência se mantém: SJF favorece curtos, PS favorece urgentes.

---

## GUI - 4 Abas

1. **Dados**: Carregar dados padrão ou JSON
2. **Simulação**: Ver SJF e PS lado a lado
   - Gantt visual
   - Tabela de resultados
   - Métricas consolidadas
3. **Comparação**: Análise automática das diferenças
4. **Sincronização**: Simular múltiplos médicos com lock

---

## Conceitos de SO Ensinados

- **Escalonamento não-preemptivo**: Uma vez escolhido, vai até o fim
- **Critérios de desempate**: Como quebrar empates
- **Morte de processo**: Se espera > life_time, processo morre
- **CPU ociosa**: Quando não há prontos
- **Race condition**: Múltiplas threads acessando recurso simultaneamente
- **Mutex/Lock**: Sincronização por exclusão mútua

---

## Checklist Pré-Apresentação

- [ ] `python gui.py` abre sem erro
- [ ] Dados padrão carregam
- [ ] Simulação executa
- [ ] Gantt aparece (SJF e PS)
- [ ] Tabelas têm dados
- [ ] Comparação funciona
- [ ] Sincronização roda
- [ ] Conheco os 5 pacientes padrão
- [ ] Memorizei respostas rápidas

---

## Como Começar

```bash
# Abrir GUI
python gui.py

# Depois:
1. Carregar Dados Padrão
2. Executar Simulação
3. Explorar as 4 abas
```

---

## Estrutura de Tempo

| Tempo | O quê |
|-------|-------|
| 0:00-2:00 | Introdução |
| 2:00-4:00 | SJF |
| 4:00-6:00 | PS |
| 6:00-7:00 | Comparação |
| 7:00-15:00 | Demo GUI + Sincronização |
| 15:00-16:00 | Conclusão + Q&A |

---

## Arquivo Importante

- `gui.py` - GUI (execute para demo)
- `schedulers.py` - Implementação dos algoritmos
- `models.py` - Estruturas de dados
- `sample_data.py` - Dados padrão (5 pacientes)
- `README.md` - Descrição técnica

---

**Pronto para apresentar!** ✓
