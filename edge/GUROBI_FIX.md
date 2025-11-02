# Gurobi DLL Error - Complete Fix Guide

## 🔍 The Error

```
ERROR: could not load library "C:\gurobi903\win64\bin\gurobi90.dll"
The specified module could not be found.
```

**Meaning:** Julia can't find the Gurobi library file, even though Gurobi appears to be installed.

---

## ✅ Solution 1: Fix Gurobi Path (If You Have License)

### Step 1: Check if Gurobi is Really There

```cmd
dir C:\gurobi903\win64\bin\gurobi90.dll
```

**If file exists:** Go to Step 2
**If file NOT found:** Reinstall Gurobi or use Solution 2 (free solver)

### Step 2: Add Gurobi to PATH

**Windows 10/11:**

1. Press **Windows Key + R**
2. Type: `sysdm.cpl` and press Enter
3. Go to **Advanced** tab → **Environment Variables**
4. Under **System Variables** (or User Variables), find **Path**
5. Click **Edit** → **New**
6. Add: `C:\gurobi903\win64\bin`
7. Click **OK** on all dialogs
8. **Restart your terminal/PowerShell**

**OR via PowerShell (temporary):**

```powershell
$env:Path += ";C:\gurobi903\win64\bin"
```

### Step 3: Verify Gurobi Works

```cmd
julia -e "using Gurobi; env = Gurobi.Env()"
```

**If this works:** Gurobi is fixed! Go run the evaluation.

**If license error:** You need a Gurobi license (see below).

### Step 4: Get Gurobi License (if needed)

**Academic (FREE):**
1. Register at: https://www.gurobi.com/academia/
2. Download license file (`gurobi.lic`)
3. Save to: `C:\gurobi903\gurobi.lic`
4. Set environment variable:
   ```cmd
   setx GRB_LICENSE_FILE "C:\gurobi903\gurobi.lic"
   ```
5. Restart terminal

**Test:**
```cmd
julia -e "using Gurobi; env = Gurobi.Env(); println(\"Gurobi works!\")"
```

---

## ✅ Solution 2: Use Free Solver (HiGHS) - RECOMMENDED FOR TESTING

**Advantage:** No license needed, open-source, works immediately

### Step 1: Install HiGHS in Julia

```cmd
julia -e "using Pkg; Pkg.add(\"HiGHS\")"
```

Wait for installation to complete (may take 2-5 minutes).

### Step 2: Modify OPF Function to Use HiGHS

**Option A: Temporary Fix (Quick Test)**

Edit `scripts/fun_centralized_OPF.jl`:

Find this line (around line 8-10):
```julia
model = Model(Gurobi.Optimizer)
```

Change to:
```julia
using HiGHS
model = Model(HiGHS.Optimizer)
set_silent(model)  # Suppress solver output
```

**Option B: Create Separate Free Version**

Keep original scripts for Gurobi, create `scripts/fun_centralized_OPF_free.jl`:

1. Copy `fun_centralized_OPF.jl` to `fun_centralized_OPF_free.jl`
2. Change Gurobi to HiGHS as shown above
3. Update edge scripts to use the free version

### Step 3: Test HiGHS

```cmd
julia -e "using HiGHS; println(\"HiGHS works!\")"
```

### Step 4: Run Evaluation

```cmd
python evaluate_edge_opf.py --mode centralized
```

---

## 🎯 Which Solution to Use?

### Use Solution 1 (Fix Gurobi) if:
- ✅ You have Gurobi license
- ✅ You need commercial-grade solver
- ✅ You're doing production research

### Use Solution 2 (HiGHS) if:
- ✅ You want to test quickly
- ✅ You don't have Gurobi license
- ✅ You want free, open-source solution
- ✅ You're just evaluating the framework

**Recommendation for now:** Use Solution 2 (HiGHS) to test the framework. You can always switch to Gurobi later.

---

## 🚀 Quick Fix for Testing (5 Minutes)

**Just want to test the framework?** Do this:

```cmd
# 1. Install HiGHS
julia -e "using Pkg; Pkg.add(\"HiGHS\")"

# 2. Edit scripts/fun_centralized_OPF.jl
# Change: model = Model(Gurobi.Optimizer)
# To:     using HiGHS
#         model = Model(HiGHS.Optimizer)
#         set_silent(model)

# 3. Do the same for scripts/fun_voltage_update.jl
# (It also creates optimization models)

# 4. Test
julia edge\scripts\opf_centralized_edge.jl

# 5. If that works, run full evaluation
cd edge
python evaluate_edge_opf.py --mode centralized
```

---

## 📝 Example: Editing fun_centralized_OPF.jl for HiGHS

**Find this section (around line 1-15):**

```julia
using PowerModels
using JuMP
using Gurobi  # ← Remove or comment this

function OPF_centralized(gen, bus, line, B, refbus)
    # create model
    model = Model(Gurobi.Optimizer)  # ← Change this line
    set_silent(model)
```

**Change to:**

```julia
using PowerModels
using JuMP
using HiGHS  # ← Add this

function OPF_centralized(gen, bus, line, B, refbus)
    # create model
    model = Model(HiGHS.Optimizer)  # ← Change this line
    set_silent(model)
```

**Save and test:**

```cmd
julia edge\scripts\opf_centralized_edge.jl
```

---

## 🔧 Advanced: Keep Both Solvers

Create a solver parameter:

```julia
# At the top of the script
SOLVER = "HiGHS"  # or "Gurobi"

if SOLVER == "Gurobi"
    using Gurobi
    optimizer = Gurobi.Optimizer
elseif SOLVER == "HiGHS"
    using HiGHS
    optimizer = HiGHS.Optimizer
else
    using GLPK
    optimizer = GLPK.Optimizer
end

# In function
model = Model(optimizer)
```

---

## ✅ Verification

After fixing, verify everything works:

```cmd
# Test Julia directly
julia edge\scripts\opf_centralized_edge.jl

# Expected output:
# ============================================================
# Starting Centralized OPF Computation
# ...
# ✓ Centralized OPF Computation completed
# Results saved to: ...

# Test Python wrapper
cd edge
python evaluate_edge_opf.py --mode centralized

# Expected output:
# ✓ Centralized OPF completed successfully
```

---

## 🆘 Still Having Issues?

**Error: "Package HiGHS not found"**
```cmd
julia -e "using Pkg; Pkg.add(\"HiGHS\")"
```

**Error: "MethodError: no method matching Model"**
- Make sure you added `using HiGHS` at the top
- Make sure you changed ALL optimization models in the file

**Error: "UndefVarError: HiGHS not defined"**
- Restart Julia
- Make sure HiGHS is installed: `julia -e "using HiGHS"`

---

## 📊 Performance Comparison

| Solver | Speed | License | Accuracy |
|--------|-------|---------|----------|
| Gurobi | Fast | Commercial/Academic | Highest |
| HiGHS | Fast | Open-Source (Free) | High |
| GLPK | Slower | Open-Source (Free) | Good |

For testing the framework, **HiGHS is perfect**. It's fast, free, and accurate.

---

## 🎯 Next Steps

1. **Install HiGHS:**
   ```cmd
   julia -e "using Pkg; Pkg.add(\"HiGHS\")"
   ```

2. **Edit `scripts/fun_centralized_OPF.jl`:**
   - Change `using Gurobi` to `using HiGHS`
   - Change `Model(Gurobi.Optimizer)` to `Model(HiGHS.Optimizer)`

3. **Edit `scripts/fun_voltage_update.jl`:**
   - Same changes as above

4. **Test:**
   ```cmd
   julia edge\scripts\opf_centralized_edge.jl
   ```

5. **Run evaluation:**
   ```cmd
   cd edge
   python evaluate_edge_opf.py --mode comparison --servers 3
   ```

**Let me know which solution you prefer!** I can help you switch to HiGHS if that's easier.
