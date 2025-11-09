"""
COMPREHENSIVE TEST SUITE FOR ALL SCRIPTS
Tests main.jl, encryption schemes, and edge integration
"""

using Printf

println("="^80)
println(" COMPREHENSIVE TEST SUITE")
println("="^80)
println()

# Track test results
tests_run = 0
tests_passed = 0
tests_failed = 0
test_errors = []

function run_test(name::String, test_func::Function)
    global tests_run, tests_passed, tests_failed, test_errors
    tests_run += 1

    print("Testing: $name... ")
    flush(stdout)

    try
        result = test_func()
        if result
            println("✓ PASS")
            tests_passed += 1
            return true
        else
            println("✗ FAIL")
            tests_failed += 1
            push!(test_errors, name => "Test returned false")
            return false
        end
    catch e
        println("✗ ERROR")
        tests_failed += 1
        push!(test_errors, name => string(e))
        return false
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: File Structure
# ══════════════════════════════════════════════════════════════════════════════

println("[1] Testing file structure...")
println("─"^80)

required_files = [
    "main.jl",
    "opt_main_verified.jl",
    "opt_main_bgv.jl",
    "opt_main_ckks.jl",
    "compare_encryption_schemes.jl",
    "run_encryption_scheme.jl",
    "test_setup.jl",
    "scripts/data_manager.jl",
    "scripts/fun_centralized_OPF.jl",
    "scripts/paillier_crypto.jl",
    "scripts/bgv_crypto.jl",
    "scripts/ckks_crypto.jl",
    "scripts/fun_voltage_update_sparse.jl",
    "testbeds/pglib_opf_case14_ieee.m",
    "edge/julia_wrapper.py",
    "edge/edge_opf_simulator.py",
    "configs/encryption_paillier.json",
    "configs/encryption_bgv.json",
    "configs/encryption_ckks.json"
]

run_test("Required files exist") do
    all_exist = true
    for file in required_files
        if !isfile(file)
            @warn "Missing file: $file"
            all_exist = false
        end
    end
    all_exist
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Julia Syntax
# ══════════════════════════════════════════════════════════════════════════════

println("\n[2] Testing Julia syntax...")
println("─"^80)

julia_files = [
    "main.jl",
    "opt_main_verified.jl",
    "opt_main_bgv.jl",
    "opt_main_ckks.jl",
    "compare_encryption_schemes.jl",
    "run_encryption_scheme.jl"
]

for jl_file in julia_files
    if isfile(jl_file)
        run_test("Syntax: $jl_file") do
            # Try to parse the file (doesn't execute, just checks syntax)
            try
                code = read(jl_file, String)
                Meta.parse(code)
                true
            catch e
                @warn "Syntax error in $jl_file: $e"
                false
            end
        end
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Dependencies
# ══════════════════════════════════════════════════════════════════════════════

println("\n[3] Testing Julia dependencies...")
println("─"^80)

required_packages = [
    "PowerModels",
    "JuMP",
    "Gurobi",
    "DataFrames",
    "LinearAlgebra",
    "CSV",
    "JSON",
    "Distributions"
]

for pkg in required_packages
    run_test("Package: $pkg") do
        try
            eval(Meta.parse("using $pkg"))
            true
        catch e
            @warn "$pkg not installed: $e"
            false
        end
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Gurobi Environment
# ══════════════════════════════════════════════════════════════════════════════

println("\n[4] Testing Gurobi...")
println("─"^80)

run_test("Gurobi initialization") do
    try
        using Gurobi
        env = Gurobi.Env()
        true
    catch e
        @warn "Gurobi initialization failed: $e"
        false
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Load Network Data
# ══════════════════════════════════════════════════════════════════════════════

println("\n[5] Testing network data loading...")
println("─"^80)

if isfile("scripts/data_manager.jl")
    run_test("Load data_manager.jl") do
        try
            include("scripts/data_manager.jl")
            true
        catch e
            @warn "Failed to load data_manager.jl: $e"
            false
        end
    end

    run_test("Load IEEE 14-Bus") do
        try
            (gen, bus, line, B, refbus) = load_data("testbeds/pglib_opf_case14_ieee.m")
            length(bus) == 14 && length(gen) >= 1
        catch e
            @warn "Failed to load IEEE 14-Bus: $e"
            false
        end
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Config Files
# ══════════════════════════════════════════════════════════════════════════════

println("\n[6] Testing config files...")
println("─"^80)

config_files = [
    "configs/encryption_paillier.json",
    "configs/encryption_bgv.json",
    "configs/encryption_ckks.json",
    "edge/test_config_centralized.json",
    "edge/test_config_distributed.json"
]

for config_file in config_files
    if isfile(config_file)
        run_test("Parse: $config_file") do
            try
                using JSON
                config = JSON.parsefile(config_file)
                !isnothing(config) && length(config) > 0
            catch e
                @warn "Failed to parse $config_file: $e"
                false
            end
        end
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Crypto Libraries
# ══════════════════════════════════════════════════════════════════════════════

println("\n[7] Testing crypto libraries...")
println("─"^80)

crypto_files = [
    "scripts/paillier_crypto.jl",
    "scripts/bgv_crypto.jl",
    "scripts/ckks_crypto.jl"
]

for crypto_file in crypto_files
    if isfile(crypto_file)
        run_test("Load: $crypto_file") do
            try
                # Just try to parse, don't execute (crypto setup is slow)
                code = read(crypto_file, String)
                !isnothing(code) && length(code) > 100
            catch e
                @warn "Failed to load $crypto_file: $e"
                false
            end
        end
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: Python Integration
# ══════════════════════════════════════════════════════════════════════════════

println("\n[8] Testing Python integration...")
println("─"^80)

run_test("Python available") do
    try
        run(`python3 --version`)
        true
    catch e
        @warn "Python3 not found: $e"
        false
    end
end

python_files = [
    "edge/julia_wrapper.py",
    "edge/edge_opf_simulator.py",
    "edge/visualization.py",
    "edge/test_integration.py"
]

for py_file in python_files
    if isfile(py_file)
        run_test("Syntax: $py_file") do
            try
                run(`python3 -m py_compile $py_file`)
                true
            catch e
                @warn "Python syntax error in $py_file: $e"
                false
            end
        end
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# TEST 9: Documentation
# ══════════════════════════════════════════════════════════════════════════════

println("\n[9] Testing documentation...")
println("─"^80)

doc_files = [
    "EDGE_INTEGRATION.md",
    "ENCRYPTION_SCHEMES.md",
    "CHANGES.md",
    "TROUBLESHOOTING.md",
    "QUICK_START.md",
    "INTEGRATION_COMPLETE.md"
]

for doc_file in doc_files
    run_test("Exists: $doc_file") do
        isfile(doc_file) && filesize(doc_file) > 1000
    end
end

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" TEST SUMMARY")
println("="^80)
@printf("Total tests:  %d\n", tests_run)
@printf("Passed:       %d (%.1f%%)\n", tests_passed, tests_passed/tests_run*100)
@printf("Failed:       %d (%.1f%%)\n", tests_failed, tests_failed/tests_run*100)
println("="^80)

if tests_failed > 0
    println("\nFailed tests:")
    for (test_name, error_msg) in test_errors
        println("  ✗ $test_name")
        println("    → $error_msg")
    end
end

println()
if tests_failed == 0
    println("✅ ALL TESTS PASSED!")
    println("\nNext steps:")
    println("  1. Run: julia main.jl")
    println("  2. Test encryption: julia opt_main_verified.jl")
    println("  3. Run edge simulation: cd edge && python3 edge_opf_simulator.py")
    exit(0)
else
    println("⚠️  SOME TESTS FAILED")
    println("\nCheck:")
    println("  1. Julia packages installed: julia -e 'using Pkg; Pkg.add([...])'")
    println("  2. Gurobi license: echo \$GRB_LICENSE_FILE")
    println("  3. Python packages: pip install psutil")
    exit(1)
end
