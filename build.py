import PyInstaller.__main__
import os

# 获取当前脚本所在目录（即项目根目录）
base_dir = os.path.dirname(os.path.abspath(__file__))

# 构造打包参数
args = [
    '--onedir',
    '--name', 'DiffExplorer',
    '--add-data', f'{os.path.join(base_dir, "R-Portable")}{os.pathsep}R-Portable',
    '--add-data', f'{os.path.join(base_dir, "run_stats.R")}{os.pathsep}.',
    '--hidden-import', 'PIL',
    '--hidden-import', 'pandas',
    '--hidden-import', 'openpyxl',
    '--hidden-import', 'matplotlib',
    '--hidden-import', 'numpy',
    os.path.join(base_dir, 'ui_main.py')
]

# 执行打包
PyInstaller.__main__.run(args)

print("\n打包完成！exe 位于 dist/DiffExplorer/ 目录下")