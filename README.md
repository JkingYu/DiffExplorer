# DiffExplorer - Differential Analysis Tool

**DiffExplorer** is a lightweight statistical differential analysis tool for biomedical researchers with zero coding background. It enables data import, statistical testing, and chart generation — with results ready right before your lab meeting. Just unzip and run!

## Features

- **Automatic test selection**: Based on normality and homogeneity of variance, automatically chooses t-test/ANOVA, Welch's test, or non-parametric tests (Mann‑Whitney U / Kruskal‑Wallis).
- **Multiple post‑hoc tests**: Supports SNK, LSD, Tukey, Dunnett, Dunn, Nemenyi, Steel, Games‑Howell, and Dunnett's T3.
- **Bar charts**: Bar charts with significance markers (*, **, ***, ns), exportable as PNG (500 DPI) and vector PDF.
- **Bilingual interface**: Switch between Chinese and English on the fly.
- **Portable & self‑contained**: No installation of R or Python required – just unzip and run.
- **Runs locally & Data privacy**: Your data never leaves your computer – no cloud upload, no privacy concerns.
- **Fully open-source**: The complete statistical R code is open-source, transparent, and reproducible.

## Quick Start

1. Download and extract `DiffExplorer.zip`.
2. Double‑click `DiffExplorer.exe` to launch.
3. Import your data (supports `.xlsx` / `.csv` / `.txt`).
4. Click "Run Analysis". (Default test pre-selected, changeable.)
5. View result tables and charts; export with one click.

## System Requirements

- Windows 10 / 11 (64‑bit)
- No additional software needed

## Download

**Option 1 (Recommended): Download from GitHub Releases**  
https://github.com/JkingYu/DiffExplorer/releases

**Option 2: Baidu Cloud (for users in China)**  
Link: https://pan.baidu.com/s/1IE-oQQ_rIkfZse4bd20Fow?pwd=kyk2  
Password: `kyk2`

## Tech Stack

- Python 3.12 (UI & plotting)
- R 4.6.1 (statistical computation)
- PyInstaller (packaging)

## Feedback

Report bugs or suggest features via Issues.

---

# DiffExplorer - 差异探索分析工具

**DiffExplorer** 是一款专为零代码基础的生物医学研究者设计的轻量级统计差异分析工具。支持数据导入、统计检验和图表生成，助你在组会前快速获得分析结果。解压即用！

## 功能特点

- **自动分流检验**：根据数据正态性和方差齐性，自动选择 t/ANOVA、Welch 或非参数检验（MW/KW）。
- **多事后检验**：支持 SNK、LSD、Tukey、Dunnett、Dunn、Nemenyi、Steel、Games‑Howell、Dunnett's T3。
- **差异柱状图**：柱状图带显著性星号(*, **, ***, ns)，支持 PNG（500 DPI）和 PDF 矢量图导出。
- **中英文切换**：界面支持中英文，适合国内外用户。
- **绿色免安装**：解压即用，无需安装 R 或 Python。
- **本地运行·数据安全**：数据无需上传云端，隐私安全。
- **全代码开源**：R 统计代码完全开源，透明可复现。

## 快速开始

1. 下载并解压 `DiffExplorer.zip`。
2. 双击 `DiffExplorer.exe` 启动。
3. 导入数据（支持 .xlsx / .csv / .txt）。
4. 点击“运行分析”。(默认方法，可调整）
5. 查看结果表格和图表，一键导出。

## 系统要求

- Windows 10 / 11（64位）
- 无需安装任何额外软件

## 下载

**方式一（推荐）：从 GitHub Releases 下载**  
https://github.com/JkingYu/DiffExplorer/releases

**方式二：百度网盘（国内用户加速）**  
通过网盘分享的文件：DiffExplorer.zip  
链接: https://pan.baidu.com/s/1IE-oQQ_rIkfZse4bd20Fow?pwd=kyk2  
提取码: `kyk2`

## 技术栈

- Python 3.12（UI 与绘图）
- R 4.6.1（统计计算）
- PyInstaller（打包）

## 反馈

欢迎通过 Issues 提交 bug 报告或建议。
