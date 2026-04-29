#!/usr/bin/env python3
"""
Demonstração: Geração de Processos Aleatórios
==============================================

Este arquivo demonstra como usar a função generate_random_processes()
para criar dados de teste com processos aleatórios.
"""

from sample_data import generate_random_processes
from schedulers import schedule_sjf, schedule_priority


def demo_random_generation():
    """Demonstra geração de dados aleatórios"""
    print("=" * 60)
    print("DEMONSTRACAO: GERACAO DE PROCESSOS ALEATORIOS")
    print("=" * 60)
    
    # Exemplo 1: Gerar 8 processos com seed fixa (reprodutível)
    print("\n[1] Exemplo 1: 8 Processos com Seed Fixa (Reproducivel)")
    print("-" * 60)
    processes = generate_random_processes(count=8, seed=42)
    print(f"Total: {len(processes)} processos\n")
    print("ID | Nome                      | Chegada | Burst | Vida | Severidade")
    print("-" * 60)
    for p in processes:
        print(f"{p.id:2} | {p.name:25} | {p.arrival_time:7} | {p.burst_time:5} | {p.life_time:4} | {p.severity_label}")
    
    # Exemplo 2: Executar simulação com dados aleatórios
    print("\n" + "=" * 60)
    print("[2] Exemplo 2: Simulacao com Dados Aleatorios")
    print("=" * 60)
    
    # Gerar novos dados aleatórios
    processes = generate_random_processes(count=6, seed=123)
    print(f"\nGerados {len(processes)} processos aleatorios\n")
    
    # SJF
    sjf_result = schedule_sjf(processes)
    print(f"SJF Results:")
    print(f"  - Processos atendidos: {len(sjf_result.records)}")
    print(f"  - Pacientes que sobreviveram: {sjf_result.survived_count}/{len(processes)}")
    print(f"  - Tempo medio de espera: {sjf_result.average_waiting_time:.2f}")
    print(f"  - Tempo medio de turnaround: {sjf_result.average_turnaround_time:.2f}")
    
    # Priority Scheduling
    ps_result = schedule_priority(processes)
    print(f"\nPriority Scheduling Results:")
    print(f"  - Processos atendidos: {len(ps_result.records)}")
    print(f"  - Pacientes que sobreviveram: {ps_result.survived_count}/{len(processes)}")
    print(f"  - Tempo medio de espera: {ps_result.average_waiting_time:.2f}")
    print(f"  - Tempo medio de turnaround: {ps_result.average_turnaround_time:.2f}")
    
    # Exemplo 3: Variação de tamanho
    print("\n" + "=" * 60)
    print("[3] Exemplo 3: Teste com Diferentes Quantidades")
    print("=" * 60)
    for count in [5, 10, 15, 20]:
        processes = generate_random_processes(count=count, seed=None)
        print(f"\n{count} processos:")
        
        sjf = schedule_sjf(processes)
        ps = schedule_priority(processes)
        
        print(f"  SJF: {sjf.survived_count}/{count} sobrevivem, espera media={sjf.average_waiting_time:.2f}")
        print(f"  PS:  {ps.survived_count}/{count} sobrevivem, espera media={ps.average_waiting_time:.2f}")


if __name__ == "__main__":
    demo_random_generation()
    print("\n" + "=" * 60)
    print("[OK] Demonstracao completa!")
    print("=" * 60)
