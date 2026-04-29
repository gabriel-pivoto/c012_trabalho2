#!/usr/bin/env python3
"""Teste para visualização de gráfico Gantt com matplotlib"""

import sys
import tkinter as tk
from tkinter import ttk

# Importar após path adjustment
from models import ScheduleResult
from sample_data import get_default_processes
from schedulers import schedule_sjf, schedule_priority
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def render_gantt_chart_test(parent, result):
    """Renderiza gráfico de Gantt visual com matplotlib (cópia da função GUI)"""
    # Limpar frame anterior
    for widget in parent.winfo_children():
        widget.destroy()
    
    try:
        # Criar figura
        fig = Figure(figsize=(12, 3), dpi=80)
        ax = fig.add_subplot(111)
        
        # Cores para os processos
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        color_map = {record.process.id: colors[i % len(colors)] 
                    for i, record in enumerate(result.records)}
        
        # Desenhar barras
        y_pos = 0
        y_labels = []
        y_ticks = []
        
        for i, record in enumerate(result.records):
            duration = record.finish_time - record.start_time
            ax.barh(y_pos, duration, left=record.start_time, height=0.6,
                   color=color_map[record.process.id], 
                   edgecolor='black', linewidth=1.5)
            
            # Label do processo
            ax.text(record.start_time + duration/2, y_pos, record.process.id,
                   va='center', ha='center', fontweight='bold', fontsize=10, color='white')
            
            y_labels.append(f"{record.process.id}")
            y_ticks.append(y_pos)
            y_pos += 1
        
        # Desenhar seções ociosas
        for block in result.gantt_blocks:
            if block.is_idle:
                for i in range(len(result.records)):
                    ax.barh(i, block.end - block.start, left=block.start, height=0.6,
                           color='lightgray', edgecolor='black', linewidth=1, alpha=0.5)
        
        # Configurar eixos
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.set_xlabel('Tempo', fontsize=11, fontweight='bold')
        ax.set_ylabel('Processos', fontsize=11, fontweight='bold')
        ax.set_title(result.algorithm_name, fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Ajustar layout
        fig.tight_layout()
        
        # Integrar com Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        print(f"✓ Gráfico {result.algorithm_name} renderizado com sucesso")
        print(f"  - {len(result.records)} processos")
        print(f"  - {len(result.gantt_blocks)} blocos Gantt")
        
    except Exception as e:
        print(f"✗ Erro ao renderizar gráfico: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Teste interativo da visualização de Gantt"""
    print("\n=== Teste de Visualização Gantt com Matplotlib ===\n")
    
    # Criar janela
    root = tk.Tk()
    root.title("Teste Gantt Visual")
    root.geometry("1000x400")
    
    # Frame principal
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Notebook com dois tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    sjf_frame = ttk.Frame(notebook)
    ps_frame = ttk.Frame(notebook)
    notebook.add(sjf_frame, text="SJF")
    notebook.add(ps_frame, text="PS")
    
    # Processos
    processes = get_default_processes()
    
    # Executar algoritmos
    sjf_result = schedule_sjf(processes)
    ps_result = schedule_priority(processes)
    
    print("Resultados:")
    print(f"  SJF: {len(sjf_result.records)} registros, {len(sjf_result.gantt_blocks)} blocos")
    print(f"  PS: {len(ps_result.records)} registros, {len(ps_result.gantt_blocks)} blocos")
    
    # Renderizar gráficos
    print("\nRenderizando gráficos...")
    render_gantt_chart_test(sjf_frame, sjf_result)
    render_gantt_chart_test(ps_frame, ps_result)
    
    print("\n✓ Teste completo! Janela deve exibir dois gráficos (SJF e PS).")
    print("  Você pode clicar entre as abas para ver cada algoritmo.")
    
    root.mainloop()


if __name__ == "__main__":
    main()
