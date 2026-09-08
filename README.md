# DiffExplorer - Differential Analysis Tool

**DiffExplorer** is a lightweight statistical differential analysis tool designed for biomedical researchers. It enables data import, statistical testing, chart generation, and result export with zero coding.

## Features

- **Automatic test selection**: Based on normality and homogeneity of variance, automatically chooses t-test/ANOVA, Welch's test, or non-parametric tests (Mann‑Whitney U / Kruskal‑Wallis).
- **Multiple post‑hoc tests**: Supports SNK, LSD, Tukey, Dunnett, Dunn, Nemenyi, Steel, Games‑Howell, and Dunnett's T3.
- **Basic bar charts**: Bar charts with significance markers (*, **, ***, ns), exportable as PNG (500 DPI) and vector PDF.
- **Bilingual interface**: Switch between Chinese and English on the fly.
- **Portable & self‑contained**: No installation of R or Python required – just unzip and run.

## Quick Start

1. Download and extract `DiffExplorer.zip`.
2. Double‑click `DiffExplorer.exe` to launch.
3. Import your data (supports `.xlsx` / `.csv` / `.txt`).
4. Configure parameters and click "Run Analysis".
5. View result tables and charts; export with one click.

## System Requirements

- Windows 10 / 11 (64‑bit)
- No additional software needed

## Download

The full package (including the R engine) is available via cloud storage:  
Shared via Baidu Cloud: DiffExplorer.zip
    Link: https://pan.baidu.com/s/1IE-oQQ_rIkfZse4bd20Fow?pwd=kyk2
    Password: kyk2

## Tech Stack

- Python 3.12 (UI & plotting)
- R 4.6.1 (statistical computation)
- PyInstaller (packaging)

---

# DiffExplorer - 差异探索分析工具

**DiffExplorer** 是一个专为生物医学研究者设计的轻量级统计差异分析工具，无需编程即可完成数据导入、统计检验、图表生成和结果导出。

## 功能特点

- **自动分流检验**：根据数据正态性和方差齐性，自动选择 t/ANOVA、Welch 或非参数检验（MW/KW）。
- **多事后检验**：支持 SNK、LSD、Tukey、Dunnett、Dunn、Nemenyi、Steel、Games‑Howell、Dunnett's T3。
- **简易柱状图**：柱状图带显著性星号(*, **, ***, ns)，支持 PNG（500 DPI）和 PDF 矢量图导出。
- **中英文切换**：界面支持中英文，适合国内外用户。
- **绿色免安装**：解压即用，无需安装 R 或 Python。

## 快速开始

1. 下载并解压 `DiffExplorer.zip`。
2. 双击 `DiffExplorer.exe` 启动。
3. 导入数据（支持 .xlsx / .csv / .txt）。
4. 设置参数后点击“运行分析”。
5. 查看结果表格和图表，一键导出。

## 系统要求

- Windows 10 / 11（64位）
- 无需安装任何额外软件

## 下载

完整版（含 R 引擎）请从网盘下载：  
通过网盘分享的文件：DiffExplorer.zip
    链接: https://pan.baidu.com/s/1IE-oQQ_rIkfZse4bd20Fow?pwd=kyk2 
    提取码: kyk2

## 技术栈

- Python 3.12（UI 与绘图）
- R 4.6.1（统计计算）
- PyInstaller（打包）
