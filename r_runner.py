import os
import sys
import json
import subprocess

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def find_rscript():
    portable_r = get_resource_path(os.path.join("R-Portable", "bin", "Rscript.exe"))
    if not os.path.exists(portable_r):
        raise FileNotFoundError(f"Rscript not found at {portable_r}")
    return portable_r

def run_r_analysis(data_path, output_dir="temp", params=None):
    if params is None:
        params = {
            "param_posthoc": "SNK",
            "welch_posthoc": "Games_Howell",
            "nonparam_posthoc": "Dunn",
            "adjust": "BH",
            "control": "A",
            "specified_pairs": [],
            "force_welch": False
        }
    os.makedirs(output_dir, exist_ok=True)
    params_path = os.path.join(output_dir, "params.json")
    with open(params_path, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)

    r_script = get_resource_path("run_stats.R")
    if not os.path.exists(r_script):
        raise FileNotFoundError(f"R script not found at {r_script}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    rscript_path = find_rscript()
    output_path = os.path.join(output_dir, "Routput.xlsx")
    cmd = [rscript_path, r_script, data_path, params_path, output_path]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                            encoding='utf-8', errors='ignore')
    if result.returncode != 0:
        print("STDERR:", result.stderr)
        raise RuntimeError("R execution failed")
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"R output not generated at {output_path}")
    return output_path

if __name__ == "__main__":
    test_data = "temp/input_R_data.xlsx"
    if not os.path.exists(test_data):
        print("Please run data_loader.py first")
    else:
        try:
            out = run_r_analysis(test_data)
            print("Success:", out)
        except Exception as e:
            print("Error:", e)