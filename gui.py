from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Sequence
import json

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models import Process, ScheduleResult, normalize_processes
from sample_data import get_default_processes, load_processes_from_json, generate_random_processes
from schedulers import schedule_sjf, schedule_priority
from metrics import build_result_rows, build_comparison_analysis
from gantt import render_gantt
from thread_sync import (
    build_patient_requests,
    suggest_initial_stock,
    run_thread_synchronization_demo,
)


class SchedulerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Simulador de Escalonamento de CPU - Hospital")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")
        
        self.processes: list[Process] = []
        self.sjf_result: ScheduleResult | None = None
        self.ps_result: ScheduleResult | None = None
        
        # Armazenar widgets dos algoritmos
        self.sjf_widgets = {}
        self.ps_widgets = {}
        
        self._create_styles()
        self._create_menu()
        self._create_widgets()
        
    def _create_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="#1f4788")
        style.configure("Subtitle.TLabel", font=("Helvetica", 12, "bold"), foreground="#333")
        style.configure("Normal.TLabel", font=("Helvetica", 10))
        
    def _create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Carregar Dados Padrão", command=self._load_default_data)
        file_menu.add_command(label="Carregar JSON", command=self._load_json_data)
        file_menu.add_command(label="Limpar", command=self._clear_data)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)
        
    def _create_widgets(self) -> None:
        # Frame principal com notebook (abas)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Abas
        self.data_frame = ttk.Frame(notebook)
        self.simulation_frame = ttk.Frame(notebook)
        self.comparison_frame = ttk.Frame(notebook)
        self.sync_frame = ttk.Frame(notebook)
        
        notebook.add(self.data_frame, text="📊 Dados")
        notebook.add(self.simulation_frame, text="⚙️ Simulação")
        notebook.add(self.comparison_frame, text="📈 Comparação")
        notebook.add(self.sync_frame, text="🔄 Sincronização")
        
        self._create_data_tab()
        self._create_simulation_tab()
        self._create_comparison_tab()
        self._create_sync_tab()
        
    def _create_data_tab(self) -> None:
        """Aba de dados de entrada"""
        frame = ttk.Frame(self.data_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title = ttk.Label(frame, text="Gerenciar Processos", style="Title.TLabel")
        title.pack(pady=(0, 10))
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="📥 Carregar Dados Padrão", 
                  command=self._load_default_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📂 Carregar JSON", 
                  command=self._load_json_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎲 Gerar Aleatórios", 
                  command=self._generate_random_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Limpar", 
                  command=self._clear_data).pack(side=tk.LEFT, padx=5)
        
        # Tabela de processos
        columns = ("ID", "Nome", "Chegada", "Duração", "Tempo Vida", "Severidade")
        self.data_tree = ttk.Treeview(frame, columns=columns, height=15, show="headings")
        
        for col in columns:
            self.data_tree.column(col, width=100, anchor=tk.CENTER)
            self.data_tree.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscroll=scrollbar.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Label de status
        self.status_label = ttk.Label(frame, text="Status: Nenhum dado carregado", 
                                      style="Normal.TLabel", foreground="#666")
        self.status_label.pack(pady=(10, 0))
        
    def _create_simulation_tab(self) -> None:
        """Aba de simulação"""
        frame = ttk.Frame(self.simulation_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="Executar Simulação", style="Title.TLabel")
        title.pack(pady=(0, 10))
        
        # Botão para simular
        ttk.Button(frame, text="▶️ Executar Simulação", 
                  command=self._run_simulation).pack(pady=(0, 10))
        
        # Notebook para os dois algoritmos
        algo_notebook = ttk.Notebook(frame)
        algo_notebook.pack(fill=tk.BOTH, expand=True)
        
        self.sjf_frame = ttk.Frame(algo_notebook)
        self.ps_frame = ttk.Frame(algo_notebook)
        
        algo_notebook.add(self.sjf_frame, text="SJF")
        algo_notebook.add(self.ps_frame, text="Menor Tempo de Vida (PS)")
        
        self._create_algorithm_view(self.sjf_frame, self.sjf_widgets)
        self._create_algorithm_view(self.ps_frame, self.ps_widgets)
        
    def _create_algorithm_view(self, parent: ttk.Frame, widget_dict: dict) -> None:
        """Cria visualização para um algoritmo"""
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Gráfico de Gantt visual (matplotlib)
        gantt_label = ttk.Label(frame, text="Diagrama de Gantt (Visual)", style="Subtitle.TLabel")
        gantt_label.pack(pady=(0, 5))
        
        # Frame para o gráfico
        chart_frame = ttk.Frame(frame)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        widget_dict['chart_frame'] = chart_frame
        
        # Gráfico de Gantt ASCII (menor)
        gantt_label_text = ttk.Label(frame, text="Diagrama ASCII", style="Subtitle.TLabel")
        gantt_label_text.pack(pady=(0, 5))
        
        gantt_text = tk.Text(frame, height=3, width=100, font=("Courier", 8))
        gantt_text.pack(fill=tk.X, pady=(0, 10))
        gantt_text.config(state=tk.DISABLED)
        widget_dict['gantt_text'] = gantt_text
        
        # Tabela de resultados
        results_label = ttk.Label(frame, text="Resultados Individuais", style="Subtitle.TLabel")
        results_label.pack(pady=(0, 5))
        
        columns = ("ID", "Nome", "Chegada", "Duração", "Vida Inicial", "Vida Final", 
                  "Início", "Fim", "Espera", "Turnaround", "Resposta", "Status")
        results_tree = ttk.Treeview(frame, columns=columns, height=6, show="headings")
        
        col_widths = [40, 60, 50, 50, 70, 70, 50, 50, 60, 80, 70, 80]
        for col, width in zip(columns, col_widths):
            results_tree.column(col, width=width, anchor=tk.CENTER)
            results_tree.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=results_tree.yview)
        results_tree.configure(yscroll=scrollbar.set)
        
        results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        widget_dict['results_tree'] = results_tree
        
        # Métricas
        metrics_label = ttk.Label(frame, text="Métricas Consolidadas", style="Subtitle.TLabel")
        metrics_label.pack(pady=(10, 5))
        
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X)
        
        metrics_text = tk.Text(metrics_frame, height=3, width=100, font=("Courier", 9))
        metrics_text.pack(fill=tk.BOTH, expand=True)
        metrics_text.config(state=tk.DISABLED)
        widget_dict['metrics_text'] = metrics_text
        
    def _create_comparison_tab(self) -> None:
        """Aba de comparação"""
        frame = ttk.Frame(self.comparison_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="Comparação de Algoritmos", style="Title.TLabel")
        title.pack(pady=(0, 10))
        
        self.comparison_text = tk.Text(frame, height=30, width=120, 
                                       font=("Courier", 9), wrap=tk.WORD)
        self.comparison_text.pack(fill=tk.BOTH, expand=True)
        self.comparison_text.config(state=tk.DISABLED)
        
    def _create_sync_tab(self) -> None:
        """Aba de sincronização de threads"""
        frame = ttk.Frame(self.sync_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="Sincronização de Threads", style="Title.TLabel")
        title.pack(pady=(0, 10))
        
        # Controles
        control_frame = ttk.LabelFrame(frame, text="Configurações", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Quantidade de Médicos (Threads):").pack(side=tk.LEFT, padx=5)
        self.doctors_spinbox = ttk.Spinbox(control_frame, from_=1, to=10, width=5)
        self.doctors_spinbox.set(3)
        self.doctors_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Estoque Inicial:").pack(side=tk.LEFT, padx=5)
        self.stock_spinbox = ttk.Spinbox(control_frame, from_=0, to=100, width=5)
        self.stock_spinbox.set(0)
        self.stock_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="(0 = automático)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="▶️ Executar Sincronização", 
                  command=self._run_sync).pack(side=tk.LEFT, padx=10)
        
        # Resultado
        self.sync_text = tk.Text(frame, height=25, width=120, 
                                font=("Courier", 9), wrap=tk.WORD)
        self.sync_text.pack(fill=tk.BOTH, expand=True)
        self.sync_text.config(state=tk.DISABLED)
        
    def _load_default_data(self) -> None:
        """Carrega dados padrão"""
        try:
            self.processes = get_default_processes()
            self._update_data_view()
            self.status_label.config(text=f"Status: {len(self.processes)} processos carregados")
            messagebox.showinfo("Sucesso", f"Dados padrão carregados: {len(self.processes)} processos")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
            
    def _load_json_data(self) -> None:
        """Carrega dados de JSON"""
        file_path = filedialog.askopenfilename(
            title="Selecione arquivo JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
            
        try:
            self.processes = load_processes_from_json(file_path)
            self._update_data_view()
            self.status_label.config(text=f"Status: {len(self.processes)} processos carregados de {Path(file_path).name}")
            messagebox.showinfo("Sucesso", f"Dados carregados: {len(self.processes)} processos")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar JSON: {str(e)}")
    
    def _generate_random_data(self) -> None:
        """Gera dados aleatórios"""
        # Criar janela de diálogo para escolher quantidade
        dialog = tk.Toplevel(self.root)
        dialog.title("Gerar Processos Aleatórios")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        
        # Centralizar
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Quantos processos deseja gerar?", 
                 font=("Arial", 10)).pack(pady=10)
        
        # Spinbox para quantidade
        quantity_var = tk.IntVar(value=8)
        spin = ttk.Spinbox(dialog, from_=1, to=50, textvariable=quantity_var, width=10)
        spin.pack(pady=5)
        
        # Checkbox para seed fixa (reprodutibilidade)
        seed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Usar seed fixa (42) para reprodutibilidade", 
                       variable=seed_var).pack(pady=5)
        
        def generate():
            try:
                count = quantity_var.get()
                seed = 42 if seed_var.get() else None
                
                self.processes = generate_random_processes(count=count, seed=seed)
                self._update_data_view()
                self.status_label.config(text=f"Status: {len(self.processes)} processos aleatórios gerados")
                messagebox.showinfo("Sucesso", f"Gerados {len(self.processes)} processos aleatórios")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar dados: {str(e)}")
        
        # Botões
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Gerar", command=generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
    def _clear_data(self) -> None:
        """Limpa dados"""
        self.processes = []
        self.sjf_result = None
        self.ps_result = None
        self.data_tree.delete(*self.data_tree.get_children())
        self.status_label.config(text="Status: Nenhum dado carregado")
        
    def _update_data_view(self) -> None:
        """Atualiza a visualização de dados"""
        self.data_tree.delete(*self.data_tree.get_children())
        for proc in self.processes:
            self.data_tree.insert("", tk.END, values=(
                proc.id,
                proc.name,
                proc.arrival_time,
                proc.burst_time,
                proc.life_time,
                proc.severity_label or "—"
            ))
            
    def _run_simulation(self) -> None:
        """Executa simulação"""
        if not self.processes:
            messagebox.showwarning("Aviso", "Carregue dados antes de simular")
            return
            
        try:
            self.sjf_result = schedule_sjf(self.processes)
            self.ps_result = schedule_priority(self.processes)
            
            self._update_algorithm_view(self.sjf_widgets, self.sjf_result)
            self._update_algorithm_view(self.ps_widgets, self.ps_result)
            
            self._update_comparison_view()
            
            messagebox.showinfo("Sucesso", "Simulação concluída!")
        except Exception as e:
            messagebox.showerror("Erro na simulação", f"Erro: {str(e)}")
            
    def _update_algorithm_view(self, widget_dict: dict, result: ScheduleResult) -> None:
        """Atualiza visualização de um algoritmo"""
        # Gantt
        gantt_text = widget_dict['gantt_text']
        gantt_text.config(state=tk.NORMAL)
        gantt_text.delete(1.0, tk.END)
        gantt_text.insert(tk.END, render_gantt(result.gantt_blocks))
        gantt_text.config(state=tk.DISABLED)
        
        # Tabela de resultados
        results_tree = widget_dict['results_tree']
        results_tree.delete(*results_tree.get_children())
        
        rows = build_result_rows(result)
        for row in rows:
            results_tree.insert("", tk.END, values=(
                row["id"],
                row["name"],
                row["arrival_time"],
                row["burst_time"],
                row["life_time_initial"],
                row["life_time_final"],
                row["start_time"],
                row["finish_time"],
                row["waiting_time"],
                row["turnaround_time"],
                row["response_time"],
                row["status_final"]
            ))
        
        # Métricas
        metrics_text = widget_dict['metrics_text']
        metrics_text.config(state=tk.NORMAL)
        metrics_text.delete(1.0, tk.END)
        
        metrics_info = f"""
Algoritmo: {result.algorithm_name}
Processos Atendidos: {len(result.records)}
Pacientes que Resistiram: {result.survived_count}
Tempo Médio de Espera: {result.average_waiting_time:.2f}
Tempo Médio de Turnaround: {result.average_turnaround_time:.2f}
Tempo Médio de Resposta: {result.average_response_time:.2f}
"""
        metrics_text.insert(tk.END, metrics_info)
        metrics_text.config(state=tk.DISABLED)
        
        # Renderizar gráfico visual
        self._render_gantt_chart(widget_dict['chart_frame'], result)
        
    def _render_gantt_chart(self, parent: ttk.Frame, result: ScheduleResult) -> None:
        """Renderiza gráfico de Gantt visual com matplotlib"""
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
            
        except Exception as e:
            print(f"Erro ao renderizar gráfico: {e}")
        
    def _update_comparison_view(self) -> None:
        """Atualiza visualização de comparação"""
        if not self.sjf_result or not self.ps_result:
            return
            
        self.comparison_text.config(state=tk.NORMAL)
        self.comparison_text.delete(1.0, tk.END)
        
        comparison = build_comparison_analysis(self.processes, self.sjf_result, self.ps_result)
        analysis_text = "\n".join(comparison)
        
        self.comparison_text.insert(tk.END, "ANÁLISE COMPARATIVA\n" + "="*50 + "\n\n")
        self.comparison_text.insert(tk.END, analysis_text)
        
        self.comparison_text.config(state=tk.DISABLED)
        
    def _run_sync(self) -> None:
        """Executa sincronização de threads"""
        if not self.sjf_result:
            messagebox.showwarning("Aviso", "Faça a simulação antes de testar sincronização")
            return
            
        try:
            doctors = int(self.doctors_spinbox.get())
            stock = int(self.stock_spinbox.get())
            if stock == 0:
                stock = None
                
            patient_requests = build_patient_requests(self.sjf_result, seed=42)
            if stock is None:
                stock = suggest_initial_stock(patient_requests)
                
            result = run_thread_synchronization_demo(patient_requests, doctors, stock, use_lock=True, seed=42)
            
            self.sync_text.config(state=tk.NORMAL)
            self.sync_text.delete(1.0, tk.END)
            
            sync_info = f"""
RESULTADO DA SINCRONIZAÇÃO (COM LOCK)
{'='*60}

Modo: {result.mode_name}
Quantidade de Médicos: {result.doctor_count}
Estoque Inicial: {result.initial_stock}
Estoque Final: {result.final_stock}

Total Solicitado: {result.total_requested} unidades
Total Concedido: {result.total_granted} unidades
Pacientes Atendidos: {result.attended_count}
Pacientes Não Atendidos: {result.not_attended_count}

Consistência Final: {"✓ OK" if result.consistency_ok else "✗ INCONSISTENTE"}
{result.consistency_details}

{'='*60}
HISTÓRICO DE ATENDIMENTOS:
"""
            self.sync_text.insert(tk.END, sync_info)
            
            for log in result.logs:
                entry = f"\nMédico {log.doctor_id} | Paciente {log.patient_id} ({log.patient_name})\n"
                entry += f"  Solicitação: {log.requested_units} unidades\n"
                entry += f"  Estoque Antes: {log.stock_before} → Depois: {log.stock_after}\n"
                entry += f"  Status: {log.status}\n"
                self.sync_text.insert(tk.END, entry)
            
            self.sync_text.config(state=tk.DISABLED)
            messagebox.showinfo("Sucesso", "Sincronização concluída!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na sincronização: {str(e)}")
            
    def _show_about(self) -> None:
        """Mostra diálogo sobre"""
        messagebox.showinfo(
            "Sobre",
            "Simulador de Escalonamento de CPU - Hospital\n\n"
            "Um sistema educacional que compara algoritmos de escalonamento\n"
            "de CPU usando a analogia de pacientes em um hospital.\n\n"
            "Algoritmos: SJF e Menor Tempo de Vida (PS)\n"
            "Sincronização: Demonstração com Threads"
        )


def main() -> None:
    root = tk.Tk()
    app = SchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
