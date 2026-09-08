import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from PIL import Image, ImageTk
import shutil
import datetime

from data_loader import smart_load
from r_runner import run_r_analysis
from plot_generator import prepare_data, plot_indicator

import sys

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ---------- 语言资源 ----------
TEXTS = {
    'zh': {
        'title': 'DiffExplorer - 差异探索分析工具_yjk',
        'file': '选择数据文件',
        'browse': '浏览',
        'preview': '预览格式',
        'param': '参数设置',
        'param_posthoc': '参数事后检验',
        'welch_posthoc': 'Welch 事后检验',
        'nonparam_posthoc': '非参数事后检验',
        'adjust': '多重校正方法',
        'control': '对照组',
        'force_welch': '强制使用 Welch',
        'specified_pairs': '指定比较组 (用 ; 分隔)',
        'specified_example': '例: A vs B; A vs C',
        'run': '运行分析',
        'results': '结果',
        'table': '统计结果',
        'chart': '图表预览',
        'export_csv': '导出 CSV',
        'export_png': '导出 PNG',
        'export_pdf': '导出 PDF',
        'no_data': '请先运行分析',
        'select_indicator': '选择指标',
        'generate_chart': '生成图表',
        'lang': '语言',
        'processing': '处理中，请稍候...',
        'done': '分析完成',
        'error': '错误',
        'ready': '就绪',
        'choose_file': '请选择文件...',
        'format_title': '输入数据格式示例',
        'format_hint': '第一行: 组名 | 第二行: 样本名 | 后续行: 变量名和数值',
        'view_horizontal': '横向格式',
        'view_vertical': '纵向格式',
        'switch_view': '切换视图',
        'confirm_export_title': '导出全部结果',
        'confirm_export_msg': '是否导出所有图表和统计结果？\n选择“是”将导出全部图片及结果文件，\n选择“否”将直接关闭并清空缓存。',
        'exporting': '正在导出全部结果...',
        'export_success': '所有结果已导出至：',
        'select_export_folder': '请选择导出文件夹',
        'export_canceled': '导出已取消，窗口保持打开。',
    },
    'en': {
        'title': 'DiffExplorer - Differential Analysis Tool _yjk',
        'file': 'Select Data File',
        'browse': 'Browse',
        'preview': 'Preview Format',
        'param': 'Parameters',
        'param_posthoc': 'Parametric Post-hoc',
        'welch_posthoc': 'Welch Post-hoc',
        'nonparam_posthoc': 'Nonparametric Post-hoc',
        'adjust': 'Multiple Correction',
        'control': 'Control Group',
        'force_welch': 'Force Welch',
        'specified_pairs': 'Specified Pairs (separated by ;)',
        'specified_example': 'e.g., A vs B; A vs C',
        'run': 'Run Analysis',
        'results': 'Results',
        'table': 'Statistics Table',
        'chart': 'Chart Preview',
        'export_csv': 'Export CSV',
        'export_png': 'Export PNG',
        'export_pdf': 'Export PDF',
        'no_data': 'Please run analysis first',
        'select_indicator': 'Select Indicator',
        'generate_chart': 'Generate Chart',
        'lang': 'Language',
        'processing': 'Processing, please wait...',
        'done': 'Analysis completed',
        'error': 'Error',
        'ready': 'Ready',
        'choose_file': 'Choose a file...',
        'format_title': 'Input Data Format Example',
        'format_hint': 'Row1: Group names | Row2: Sample names | Following rows: Variable names and values',
        'view_horizontal': 'Horizontal Format',
        'view_vertical': 'Vertical Format',
        'switch_view': 'Switch View',
        'confirm_export_title': 'Export All Results',
        'confirm_export_msg': 'Export all charts and results?\n"Yes" will export all images and result file,\n"No" will close and clear cache.',
        'exporting': 'Exporting all results...',
        'export_success': 'All results exported to:',
        'select_export_folder': 'Select Export Folder',
        'export_canceled': 'Export canceled, window remains open.',
    }
}

class DiffExplorerApp:
    def __init__(self, root):
        self.root = root
        self.lang = 'zh'
        self.data_path = None
        self.result_path = None
        self.long_data = None
        self.res_df = None
        self.group_order = None
        self.indicators = None
        self.current_indicator = None
        self.preview_image = None
        self._updating = False

        self.root.title(TEXTS[self.lang]['title'])
        self.root.geometry('1100x700')
        self.root.minsize(900, 600)
        self.root.configure(bg='#f0f4f8')

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.font_family = 'Source Han Sans SC' if self.lang == 'zh' else 'Source Han Sans'
        try:
            from tkinter import font
            available = [f.lower() for f in font.families()]
            if 'source han sans sc' not in available and 'source han sans' not in available:
                self.font_family = 'Microsoft YaHei' if self.lang == 'zh' else 'Arial'
        except:
            self.font_family = 'Microsoft YaHei' if self.lang == 'zh' else 'Arial'

        self._configure_style()
        self._build_ui()
        self._apply_language()
        self._setup_dynamic_visibility()
        self._bind_combobox_events()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        bg_color = '#f0f4f8'
        fg_color = '#2c3e50'
        select_color = '#3498db'

        style.configure('.', background=bg_color, foreground=fg_color, font=(self.font_family, 9))
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe', background=bg_color, borderwidth=1, relief='solid', bordercolor='#d0d7de')
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color, font=(self.font_family, 10, 'bold'))

        style.configure('TButton', padding=6, relief='flat', background='#e8edf2', foreground=fg_color, borderwidth=0)
        style.map('TButton', background=[('active', '#d5dde6'), ('pressed', '#c0cbd8')])

        style.configure('Accent.TButton', padding=6, relief='flat', background=select_color, foreground='white', borderwidth=0)
        style.map('Accent.TButton', background=[('active', '#2980b9'), ('pressed', '#1f6a9a')])

        style.configure('TEntry', fieldbackground='white', borderwidth=1, relief='solid', bordercolor='#d0d7de')
        style.configure('TCombobox', fieldbackground='white', borderwidth=1, relief='solid', bordercolor='#d0d7de')

        style.configure('TNotebook', background=bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', padding=[12, 4], background='#e8edf2', foreground=fg_color)
        style.map('TNotebook.Tab', background=[('selected', 'white'), ('active', '#d5dde6')])

        style.configure('TPanedWindow', background=bg_color, sashrelief='flat', sashthickness=4)

        style.configure('Treeview', background='white', fieldbackground='white', foreground=fg_color, borderwidth=0)
        style.configure('Treeview.Heading', background='#e8edf2', foreground=fg_color, font=(self.font_family, 9, 'bold'))
        style.map('Treeview', background=[('selected', select_color)])

        style.configure('Status.TLabel', background='#e8edf2', relief='sunken', anchor='w')

    def _build_ui(self):
        self.pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = ttk.Frame(self.pane, width=320)
        self.pane.add(self.left_frame, weight=0)

        lang_frame = ttk.Frame(self.left_frame)
        lang_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(lang_frame, text='Language:').pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value='中文')
        lang_menu = ttk.Combobox(lang_frame, textvariable=self.lang_var,
                                 values=['中文', 'English'], state='readonly', width=12)
        lang_menu.pack(side=tk.RIGHT)
        lang_menu.bind('<<ComboboxSelected>>', self._switch_lang)

        file_frame = ttk.LabelFrame(self.left_frame, text='Data File', padding=5)
        file_frame.pack(fill=tk.X, pady=5)
        self.file_path_var = tk.StringVar(value=TEXTS[self.lang]['choose_file'])
        ttk.Entry(file_frame, textvariable=self.file_path_var).pack(fill=tk.X, padx=5, pady=2)
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.browse_btn = ttk.Button(btn_frame, text=TEXTS[self.lang]['browse'], command=self._browse_file)
        self.browse_btn.pack(side=tk.LEFT, padx=2)
        self.preview_btn = ttk.Button(btn_frame, text=TEXTS[self.lang]['preview'], command=self._preview_format)
        self.preview_btn.pack(side=tk.LEFT, padx=2)

        param_frame = ttk.LabelFrame(self.left_frame, text='Parameters', padding=5)
        param_frame.pack(fill=tk.X, pady=5)
        self.param_grid = ttk.Frame(param_frame)
        self.param_grid.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(self.param_grid, text='Parametric Post-hoc:').grid(row=0, column=0, sticky=tk.W, pady=2)
        self.param_posthoc_var = tk.StringVar(value='SNK')
        self.param_posthoc_cb = ttk.Combobox(self.param_grid, textvariable=self.param_posthoc_var,
                                             values=['LSD', 'SNK', 'Tukey', 'Dunnett'], state='readonly', width=18)
        self.param_posthoc_cb.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        self.welch_label = ttk.Label(self.param_grid, text='Welch Post-hoc:')
        self.welch_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        self.welch_posthoc_var = tk.StringVar(value='Games_Howell')
        self.welch_cb = ttk.Combobox(self.param_grid, textvariable=self.welch_posthoc_var,
                                     values=['Games_Howell', 'Dunnett_T3'], state='readonly', width=18)
        self.welch_cb.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.welch_label.grid_remove()
        self.welch_cb.grid_remove()

        ttk.Label(self.param_grid, text='Nonparametric Post-hoc:').grid(row=2, column=0, sticky=tk.W, pady=2)
        self.nonparam_posthoc_var = tk.StringVar(value='Dunn')
        self.nonparam_cb = ttk.Combobox(self.param_grid, textvariable=self.nonparam_posthoc_var,
                                        values=['Dunn', 'Nemenyi', 'Steel'], state='readonly', width=18)
        self.nonparam_cb.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        self.adjust_label = ttk.Label(self.param_grid, text='Adjustment:')
        self.adjust_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        self.adjust_var = tk.StringVar(value='BH')
        self.adjust_cb = ttk.Combobox(self.param_grid, textvariable=self.adjust_var,
                                      values=['BH', 'Holm', 'Bonferroni'], state='readonly', width=18)
        self.adjust_cb.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        self.adjust_label.grid_remove()
        self.adjust_cb.grid_remove()

        self.control_label = ttk.Label(self.param_grid, text='Control Group:')
        self.control_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        self.control_var = tk.StringVar()
        self.control_entry = ttk.Entry(self.param_grid, textvariable=self.control_var, width=18)
        self.control_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        self.control_label.grid_remove()
        self.control_entry.grid_remove()

        self.spec_label = ttk.Label(self.param_grid, text='Specified Pairs:')
        self.spec_label.grid(row=5, column=0, sticky=tk.W, pady=2)
        self.spec_var = tk.StringVar()
        self.spec_entry = ttk.Entry(self.param_grid, textvariable=self.spec_var, width=18)
        self.spec_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=2)
        self.spec_label.grid_remove()
        self.spec_entry.grid_remove()
        self.spec_hint = ttk.Label(self.param_grid, text='e.g., A vs B; A vs C', font=('', 8))
        self.spec_hint.grid(row=6, column=1, sticky=tk.W, padx=5)
        self.spec_hint.grid_remove()

        self.force_welch_var = tk.IntVar()
        self.force_welch_cb = ttk.Checkbutton(self.param_grid, text='Force Welch',
                                              variable=self.force_welch_var,
                                              command=self._on_force_welch_toggle)
        self.force_welch_cb.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.run_btn = ttk.Button(self.left_frame, text='Run Analysis', style='Accent.TButton', command=self._run_analysis)
        self.run_btn.pack(fill=tk.X, pady=15)

        self.status_var = tk.StringVar(value='Ready')
        status_label = ttk.Label(self.left_frame, textvariable=self.status_var, style='Status.TLabel')
        status_label.pack(fill=tk.X, pady=(0,5))

        self.right_frame = ttk.Frame(self.pane)
        self.pane.add(self.right_frame, weight=1)

        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text='Table')
        self.tree = ttk.Treeview(self.table_frame, show='headings')
        self.tree.pack(fill=tk.BOTH, expand=True)
        scroll_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        table_export_frame = ttk.Frame(self.table_frame)
        table_export_frame.pack(fill=tk.X, pady=8)
        self.export_csv_btn = ttk.Button(table_export_frame, text='Export CSV', command=self._export_csv)
        self.export_csv_btn.pack(side=tk.LEFT, padx=5)

        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text='Chart')

        ind_frame = ttk.Frame(self.chart_frame)
        ind_frame.pack(fill=tk.X, pady=8)
        ttk.Label(ind_frame, text='Indicator:').pack(side=tk.LEFT, padx=5)
        self.indicator_var = tk.StringVar()
        self.ind_combo = ttk.Combobox(ind_frame, textvariable=self.indicator_var, state='readonly', width=35)
        self.ind_combo.pack(side=tk.LEFT, padx=5)
        self.gen_chart_btn = ttk.Button(ind_frame, text='Generate Chart', style='Accent.TButton', command=self._generate_chart)
        self.gen_chart_btn.pack(side=tk.LEFT, padx=5)

        self.image_label = ttk.Label(self.chart_frame, background='white')
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        chart_export_frame = ttk.Frame(self.chart_frame)
        chart_export_frame.pack(fill=tk.X, pady=8)
        self.export_png_btn = ttk.Button(chart_export_frame, text='Export PNG', command=self._export_png)
        self.export_png_btn.pack(side=tk.LEFT, padx=5)
        self.export_pdf_btn = ttk.Button(chart_export_frame, text='Export PDF', command=self._export_pdf)
        self.export_pdf_btn.pack(side=tk.LEFT, padx=5)

    # ---------- 关闭窗口事件 ----------
    def _on_closing(self):
        if self.res_df is None or self.res_df.empty:
            self._clean_temp()
            self.root.destroy()
            return

        title = TEXTS[self.lang]['confirm_export_title']
        msg = TEXTS[self.lang]['confirm_export_msg']
        answer = messagebox.askyesno(title, msg)
        if answer:
            self.status_var.set(TEXTS[self.lang]['exporting'])
            self.root.update()
            export_dir = self._export_all_results()
            if export_dir is None:
                # 用户取消了文件夹选择，窗口保持打开
                messagebox.showinfo(TEXTS[self.lang]['export_canceled'], TEXTS[self.lang]['export_canceled'])
                self.status_var.set(TEXTS[self.lang]['ready'])
                return
            else:
                messagebox.showinfo(TEXTS[self.lang]['export_success'], f"{export_dir}")
        # 清理并关闭
        self._clean_temp()
        self.root.destroy()

    def _clean_temp(self):
        for dir_name in ['temp', 'figures']:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name, ignore_errors=True)

    def _export_all_results(self):
        # 让用户选择保存文件夹
        folder = filedialog.askdirectory(title=TEXTS[self.lang]['select_export_folder'])
        if not folder:
            return None  # 用户取消
        # 创建时间戳子文件夹
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        export_dir = os.path.join(folder, f'Exported_Results_{timestamp}')
        os.makedirs(export_dir, exist_ok=True)

        # 复制结果文件
        if self.result_path and os.path.exists(self.result_path):
            shutil.copy(self.result_path, os.path.join(export_dir, 'Routput.xlsx'))

        # 生成所有指标的图表
        if self.long_data is not None and self.res_df is not None and self.indicators:
            for ind in self.indicators:
                try:
                    plot_indicator(
                        ind, self.long_data, self.res_df, 'Blue', export_dir, self.group_order
                    )
                except Exception as e:
                    print(f"Failed to generate chart for {ind}: {e}")
        return export_dir

    # ---------- 其余功能 ----------
    def _bind_combobox_events(self):
        self.param_posthoc_cb.bind('<<ComboboxSelected>>', self._on_combobox_change)
        self.welch_cb.bind('<<ComboboxSelected>>', self._on_combobox_change)
        self.nonparam_cb.bind('<<ComboboxSelected>>', self._on_combobox_change)

    def _on_combobox_change(self, event=None):
        if self._updating:
            return
        self._updating = True
        param = self.param_posthoc_var.get()
        welch = self.welch_posthoc_var.get()
        nonparam = self.nonparam_posthoc_var.get()

        widget = event.widget if event else None
        if widget == self.param_posthoc_cb:
            changed_val = param
        elif widget == self.welch_cb:
            changed_val = welch
        elif widget == self.nonparam_cb:
            changed_val = nonparam
        else:
            changed_val = None

        special = {'Dunnett', 'Dunnett_T3', 'Steel'}
        if changed_val in special:
            if changed_val == 'Dunnett':
                self.welch_posthoc_var.set('Dunnett_T3')
                self.nonparam_posthoc_var.set('Steel')
            elif changed_val == 'Dunnett_T3':
                self.param_posthoc_var.set('Dunnett')
                self.nonparam_posthoc_var.set('Steel')
            elif changed_val == 'Steel':
                self.param_posthoc_var.set('Dunnett')
                self.welch_posthoc_var.set('Dunnett_T3')
        self._updating = False
        self._update_visibility()

    def _setup_dynamic_visibility(self):
        self._update_visibility()

    def _on_force_welch_toggle(self):
        self._update_visibility()

    def _update_visibility(self):
        show_welch = bool(self.force_welch_var.get())
        if show_welch:
            self.welch_label.grid()
            self.welch_cb.grid()
        else:
            self.welch_label.grid_remove()
            self.welch_cb.grid_remove()

        show_adjust = (self.param_posthoc_var.get() == 'LSD' or
                       self.nonparam_posthoc_var.get() == 'Dunn')
        if show_adjust:
            self.adjust_label.grid()
            self.adjust_cb.grid()
        else:
            self.adjust_label.grid_remove()
            self.adjust_cb.grid_remove()

        show_spec = (self.param_posthoc_var.get() == 'LSD')
        if show_spec:
            self.spec_label.grid()
            self.spec_entry.grid()
            self.spec_hint.grid()
        else:
            self.spec_label.grid_remove()
            self.spec_entry.grid_remove()
            self.spec_hint.grid_remove()

        special = {'Dunnett', 'Dunnett_T3', 'Steel'}
        visible_values = [self.param_posthoc_var.get()]
        if self.force_welch_var.get():
            visible_values.append(self.welch_posthoc_var.get())
        visible_values.append(self.nonparam_posthoc_var.get())
        show_control = any(v in special for v in visible_values)
        if show_control:
            self.control_label.grid()
            self.control_entry.grid()
        else:
            self.control_label.grid_remove()
            self.control_entry.grid_remove()

    def _switch_lang(self, event=None):
        self.lang = 'zh' if self.lang_var.get() == '中文' else 'en'
        self._apply_language()
        self.font_family = 'Source Han Sans SC' if self.lang == 'zh' else 'Source Han Sans'
        self.root.title(TEXTS[self.lang]['title'])

    def _apply_language(self):
        t = TEXTS[self.lang]
        self.file_path_var.set(t['choose_file'])
        self.browse_btn.config(text=t['browse'])
        self.preview_btn.config(text=t['preview'])
        self.run_btn.config(text=t['run'])
        self.notebook.tab(0, text=t['table'])
        self.notebook.tab(1, text=t['chart'])
        self.gen_chart_btn.config(text=t['generate_chart'])
        self.export_csv_btn.config(text=t['export_csv'])
        self.export_png_btn.config(text=t['export_png'])
        self.export_pdf_btn.config(text=t['export_pdf'])
        self.force_welch_cb.config(text=t['force_welch'])

    def _preview_format(self):
        win = tk.Toplevel(self.root)
        win.title(TEXTS[self.lang]['format_title'])
        win.geometry('500x300')
        win.configure(bg='#f0f4f8')
        self.preview_view = 'horizontal'
        def switch_view():
            self.preview_view = 'vertical' if self.preview_view == 'horizontal' else 'horizontal'
            update_preview()
        btn = ttk.Button(win, text=TEXTS[self.lang]['switch_view'], style='Accent.TButton', command=switch_view)
        btn.pack(pady=5)
        text_widget = tk.Text(win, wrap=tk.NONE, font=('Courier', 10), bg='white', fg='#2c3e50')
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        hint_label = ttk.Label(win, text=TEXTS[self.lang]['format_hint'], background='#f0f4f8')
        hint_label.pack(pady=5)

        def update_preview():
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            if self.preview_view == 'horizontal':
                sample = [
                    ["Groups", "A", "A", "B", "B"],
                    ["Samples", "A1", "A2", "B1", "B2"],
                    ["data.001", "3.14", "1.59", "2.65", "3.58"]
                ]
                view_text = TEXTS[self.lang]['view_horizontal']
            else:
                sample = [
                    ["Groups", "Samples", "data.001"],
                    ["A", "A1", "3.14"],
                    ["A", "A2", "1.59"],
                    ["B", "B1", "2.65"],
                    ["B", "B2", "3.58"]
                ]
                view_text = TEXTS[self.lang]['view_vertical']
            text_widget.insert(tk.END, f"{view_text}\n\n")
            col_widths = [max(len(str(row[i])) for row in sample) for i in range(len(sample[0]))]
            for row in sample:
                line = "  ".join(str(item).ljust(col_widths[i]) for i, item in enumerate(row))
                text_widget.insert(tk.END, line + "\n")
            text_widget.config(state=tk.DISABLED)
        update_preview()

    def _browse_file(self):
        path = filedialog.askopenfilename(
            filetypes=[('Excel files', '*.xlsx *.xls'), ('CSV files', '*.csv'), ('Text files', '*.txt')]
        )
        if path:
            self.file_path_var.set(path)
            self.data_path = path

    def _run_analysis(self):
        if not self.data_path:
            messagebox.showerror(TEXTS[self.lang]['error'], 'Please select a data file first.')
            return
        self.run_btn.config(state=tk.DISABLED)
        self.status_var.set(TEXTS[self.lang]['processing'])
        threading.Thread(target=self._run_analysis_thread, daemon=True).start()

    def _run_analysis_thread(self):
        try:
            data_file = smart_load(self.data_path, output_dir='temp')
            params = {
                'param_posthoc': self.param_posthoc_var.get(),
                'welch_posthoc': self.welch_posthoc_var.get(),
                'nonparam_posthoc': self.nonparam_posthoc_var.get(),
                'adjust': self.adjust_var.get(),
                'control': self.control_var.get().strip() or None,
                'specified_pairs': self._parse_specified_pairs(self.spec_var.get()),
                'force_welch': bool(self.force_welch_var.get())
            }
            result_path = run_r_analysis(data_file, output_dir='temp', params=params)
            self.result_path = result_path
            self.long_data, self.res_df, self.group_order, self.indicators = prepare_data(data_file, result_path)
            self.root.after(0, self._update_after_run)
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: self._show_error(err_msg))

    def _parse_specified_pairs(self, text):
        if not text.strip():
            return []
        pairs = []
        for part in text.split(';'):
            part = part.strip()
            if ' vs ' in part:
                g1, g2 = part.split(' vs ')
                pairs.append([g1.strip(), g2.strip()])
        return pairs

    def _update_after_run(self):
        self._update_table()
        if self.indicators:
            self.ind_combo['values'] = self.indicators
            self.indicator_var.set(self.indicators[0])
        self.run_btn.config(state=tk.NORMAL)
        self.status_var.set(TEXTS[self.lang]['done'])

    def _update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.res_df is None or self.res_df.empty:
            return
        cols = list(self.res_df.columns)
        self.tree['columns'] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.W)
        for _, row in self.res_df.iterrows():
            self.tree.insert('', tk.END, values=list(row))

    def _generate_chart(self):
        if self.long_data is None or self.res_df is None:
            messagebox.showinfo('Info', TEXTS[self.lang]['no_data'])
            return
        ind = self.indicator_var.get()
        if not ind:
            return
        self.status_var.set(f'Generating chart for {ind}...')
        try:
            png_path, pdf_path = plot_indicator(
                ind, self.long_data, self.res_df, 'Blue', 'figures', self.group_order
            )
            img = Image.open(png_path)
            img.thumbnail((800, 600))
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            self.current_indicator = ind
            self.current_png = png_path
            self.current_pdf = pdf_path
            self.status_var.set('Chart generated')
        except Exception as e:
            self._show_error(str(e))

    def _export_csv(self):
        if self.res_df is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if path:
            self.res_df.to_csv(path, index=False)

    def _export_png(self):
        if hasattr(self, 'current_png') and os.path.exists(self.current_png):
            path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
            if path:
                shutil.copy(self.current_png, path)

    def _export_pdf(self):
        if hasattr(self, 'current_pdf') and os.path.exists(self.current_pdf):
            path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
            if path:
                shutil.copy(self.current_pdf, path)

    def _show_error(self, msg):
        messagebox.showerror(TEXTS[self.lang]['error'], msg)
        self.run_btn.config(state=tk.NORMAL)
        self.status_var.set('Error')

if __name__ == '__main__':
    root = tk.Tk()
    app = DiffExplorerApp(root)
    root.mainloop()