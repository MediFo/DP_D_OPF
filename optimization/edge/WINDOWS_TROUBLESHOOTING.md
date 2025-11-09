# Windows Troubleshooting Guide

## ✅ Fixed: Path Issues on Windows

**Version 06281b6 and earlier** had Unix-style paths that didn't work on Windows.
**Latest version** uses Julia's `joinpath()` and `@__DIR__` for cross-platform compatibility.

If you pulled the latest code (after this commit), the path issues should be fixed!

---

## 🔍 Diagnosing Failures

### Step 1: Run the Debug Script

```bash
cd edge
python debug_failures.py
```

This will show you **exactly** why the Julia nodes failed.

### Step 2: Common Errors and Solutions

---

## 🐛 Common Windows Issues

### Issue 1: "Julia not found" or "julia: command not found"

**Error in debug output:**
```
FileNotFoundError: [WinError 2] The system cannot find the file specified: 'julia'
```

**Solution:**

1. Check if Julia is installed:
   ```cmd
   julia --version
   ```

2. If not found, add Julia to PATH:
   ```cmd
   # Find where Julia is installed (e.g., C:\Users\YourName\AppData\Local\Programs\Julia-1.9.3\bin)

   # Add to PATH temporarily:
   set PATH=%PATH%;C:\Users\YourName\AppData\Local\Programs\Julia-1.9.3\bin

   # Or permanently via System Properties > Environment Variables
   ```

3. Verify:
   ```cmd
   julia --version
   ```

---

### Issue 2: "cannot load such file -- ../../scripts/data_manager.jl"

**This was the main problem!** Now fixed in latest version.

**Error in debug output:**
```
ERROR: LoadError: could not open file ../../scripts/data_manager.jl
```

**Solution:**

Pull the latest code - it uses absolute paths now:
```bash
git pull origin claude/edge-device-evaluation-011CUi3Sxn7ZKMHFNPBXsfNE
```

If still having issues, the Julia scripts now print diagnostic info:
```
Julia working directory: C:\Users\...
Script directory: C:\Users\...\edge\scripts
Project root: C:\Users\...\DP_D_OPF
```

Check that "Project root" points to your DP_D_OPF folder.

---

### Issue 3: "Case file not found"

**Error in debug output:**
```
ERROR: Case file not found: testbeds/pglib_opf_case14_ieee.m
```

**Solution:**

Make sure you're running from the correct directory:

```bash
# Should be in DP_D_OPF root, not in edge/
cd C:\Users\YourName\Desktop\PSDO\DP_D_OPF-claude-...

# Then run from edge subdirectory
cd edge
python evaluate_edge_opf.py --mode centralized
```

Or use absolute paths in config files.

---

### Issue 4: Gurobi License Error

**Error in debug output:**
```
ERROR: No Gurobi license found
```

**Solution:**

**Option A: Get Gurobi License (Free for academics)**
1. Register at: https://www.gurobi.com/academia/
2. Download license file
3. Set environment variable:
   ```cmd
   set GRB_LICENSE_FILE=C:\path\to\gurobi.lic
   ```

**Option B: Use Free Solver (GLPK)**
You can modify the Julia scripts to use a free solver:

1. Open `scripts/fun_centralized_OPF.jl`
2. Change:
   ```julia
   # Old:
   model = Model(Gurobi.Optimizer)

   # New:
   using GLPK
   model = Model(GLPK.Optimizer)
   ```

3. Install GLPK in Julia:
   ```julia
   julia> using Pkg
   julia> Pkg.add("GLPK")
   ```

---

### Issue 5: Missing Julia Packages

**Error in debug output:**
```
ERROR: ArgumentError: Package PowerModels not found
```

**Solution:**

Install required packages in Julia:

```julia
# Open Julia REPL
julia

# Install packages
using Pkg
Pkg.add("PowerModels")
Pkg.add("JuMP")
Pkg.add("Gurobi")  # or Pkg.add("GLPK") for free solver
Pkg.add("DataFrames")
Pkg.add("CSV")
Pkg.add("Distributions")
Pkg.add("JSON")
Pkg.add("DataStructures")
```

Or install all at once:
```julia
Pkg.add(["PowerModels", "JuMP", "Gurobi", "DataFrames", "CSV", "Distributions", "JSON", "DataStructures"])
```

---

### Issue 6: Python Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'psutil'
```

**Solution:**

```cmd
pip install psutil numpy matplotlib
```

Or:
```cmd
pip install -r requirements.txt
```

---

### Issue 7: Permission Denied (results/ or plots/)

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'results'
```

**Solution:**

```cmd
# Make sure directories exist and are writable
cd edge
mkdir results plots
```

Or run as administrator (right-click Command Prompt > Run as Administrator)

---

### Issue 8: Backslash Issues in Paths

**Error in debug output:**
```
ERROR: SystemError: opening file "C:\Users\...\edge\scripts\opf_edge_node.jl": Invalid argument
```

**Solution:**

This should be fixed in the latest version. If still occurring, manually edit the Python wrapper to use raw strings:

```python
# In julia_wrapper.py
cmd = ["julia", str(script_path), str(config_file)]
# Make sure all paths are absolute
```

---

## 🧪 Step-by-Step Testing

### Test 1: Verify Julia Works

```cmd
julia --version
```

Expected output:
```
julia version 1.9.3
```

### Test 2: Test Julia Script Directly

```cmd
cd C:\Users\...\DP_D_OPF-claude-...
julia edge\scripts\opf_centralized_edge.jl
```

This should run and output:
```
============================================================
Starting Centralized OPF Computation
...
Results saved to: ...
```

If this works, Julia is fine. If not, check error message.

### Test 3: Test Python Wrapper

```cmd
cd edge
python -c "from julia_wrapper import JuliaOPFExecutor; print('OK')"
```

Expected output: `OK`

### Test 4: Test Centralized Mode

```cmd
python evaluate_edge_opf.py --mode centralized
```

This should complete without errors. Check for:
```
✓ Centralized OPF completed successfully
```

### Test 5: Test Single Distributed Node

```cmd
python evaluate_edge_opf.py --mode distributed --servers 1
```

If this works, try more servers.

### Test 6: Test Full Distributed

```cmd
python evaluate_edge_opf.py --mode distributed --servers 3
```

All nodes should succeed:
```
✓ Node 1 completed successfully
✓ Node 2 completed successfully
✓ Node 3 completed successfully
```

---

## 📋 Checklist

Before running, ensure:

- [ ] Julia installed and in PATH (`julia --version` works)
- [ ] Julia packages installed (see Issue 5)
- [ ] Gurobi licensed OR using free solver (see Issue 4)
- [ ] Python packages installed (`pip install psutil numpy matplotlib`)
- [ ] In correct directory (DP_D_OPF root, then cd to edge)
- [ ] Latest code pulled (with path fixes)
- [ ] Can run: `julia edge\scripts\opf_centralized_edge.jl` directly

---

## 🔧 Quick Fix Commands

```cmd
# Setup Julia packages
julia -e "using Pkg; Pkg.add([\"PowerModels\", \"JuMP\", \"Gurobi\", \"DataFrames\", \"CSV\", \"Distributions\", \"JSON\", \"DataStructures\"])"

# Setup Python packages
pip install psutil numpy matplotlib

# Add Julia to PATH (adjust path to your installation)
set PATH=%PATH%;C:\Users\YourName\AppData\Local\Programs\Julia-1.9.3\bin

# Test Julia
julia --version

# Test direct execution
cd C:\Users\...\DP_D_OPF-claude-...
julia edge\scripts\opf_centralized_edge.jl

# Run evaluation
cd edge
python evaluate_edge_opf.py --mode centralized
```

---

## 📊 After Success

Once working, you should see:

```
results/
├── centralized_20251102_*.json
├── centralized_20251102_*_full.json
├── centralized_20251102_*_summary.csv
└── ...

plots/
├── centralized_20251102_*_server_resources.png
└── ...
```

---

## 🆘 Still Having Issues?

1. Run `python debug_failures.py` to see exact error
2. Check the error message carefully
3. Match it to issues above
4. Make sure you pulled latest code (path fixes)
5. Try running Julia script directly first
6. Use `--sequential` flag to run nodes one at a time

---

## 💡 Windows-Specific Tips

1. **Use Command Prompt or PowerShell**, not Git Bash (path issues)

2. **Absolute paths work better** on Windows:
   ```cmd
   python evaluate_edge_opf.py --case C:\full\path\to\case14_ieee.m
   ```

3. **Backslashes in Python**: The code handles this automatically now

4. **Long paths**: If paths are too long, move repo closer to C:\
   ```cmd
   # Bad: C:\Users\LongUserName\Desktop\Projects\Research\OPF\DP_D_OPF-claude-...
   # Good: C:\OPF\DP_D_OPF
   ```

5. **Antivirus**: May slow down or block Julia processes. Add exception if needed.

---

## ✅ Verification

Run this to verify everything is working:

```cmd
cd edge
python quick_test.py
```

Should show all green checkmarks:
```
✓ All Python dependencies found
✓ Julia found
✓ All framework modules loaded successfully
✓ Simulation ready
```

Then:
```cmd
python evaluate_edge_opf.py --mode comparison --servers 3
```

Success output:
```
✓ Centralized OPF completed successfully
✓ Node 1 completed successfully
✓ Node 2 completed successfully
✓ Node 3 completed successfully
✓ Evaluation completed successfully!
```

---

## 📞 Need More Help?

The updated Julia scripts now print diagnostic information:
- Working directory
- Script directory
- Project root

This helps identify path issues. Check the console output when running.
