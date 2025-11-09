"""
ENCRYPTION SCHEME RUNNER
Unified wrapper to run OPF with different homomorphic encryption schemes

Supported schemes:
- paillier: Partial HE (addition only), fastest encryption
- bgv: Fully HE (addition + multiplication), integer-based
- ckks: Fully HE (addition + multiplication), real number support

Usage:
    julia run_encryption_scheme.jl config.json

Config file should include:
{
  "encryption_scheme": "paillier",  // or "bgv", "ckks"
  "caseID": "testbeds/pglib_opf_case14_ieee.m",
  "max_iterations": 1000,
  "rho": 10.0,
  "tolerance": 0.01,
  ...
}
"""

using JSON

function main()
    if length(ARGS) == 0
        println("❌ Error: Config file required")
        println("\nUsage:")
        println("  julia run_encryption_scheme.jl config.json")
        println("\nExample config.json:")
        println("""
        {
          "encryption_scheme": "paillier",
          "caseID": "testbeds/pglib_opf_case14_ieee.m",
          "max_iterations": 1000,
          "rho": 10.0,
          "tolerance": 0.01
        }
        """)
        return
    end

    config_file = ARGS[1]

    if !isfile(config_file)
        println("❌ Error: Config file not found: $config_file")
        return
    end

    config = JSON.parsefile(config_file)
    scheme = get(config, "encryption_scheme", "paillier")

    println("="^80)
    println(" RUNNING OPF WITH HOMOMORPHIC ENCRYPTION")
    println("="^80)
    println("Encryption scheme: $scheme")
    println("Config file: $config_file")
    println("="^80 * "\n")

    # Map scheme to corresponding script
    script_map = Dict(
        "paillier" => "opt_main_verified.jl",
        "bgv" => "opt_main_bgv.jl",
        "ckks" => "opt_main_ckks.jl"
    )

    if !haskey(script_map, scheme)
        println("❌ Error: Unknown encryption scheme '$scheme'")
        println("Supported schemes: paillier, bgv, ckks")
        return
    end

    script_file = script_map[scheme]

    if !isfile(script_file)
        println("❌ Error: Encryption script not found: $script_file")
        println("Make sure all encryption scheme files are in the optimization/ folder")
        return
    end

    println("📂 Loading encryption script: $script_file\n")

    # Note: The standalone scripts don't currently accept config files
    # They use hardcoded parameters
    # This wrapper documents how to integrate them in the future

    println("⚠️  Note: Standalone encryption scripts use hardcoded parameters.")
    println("To customize parameters, edit the script file directly:")
    println("  $script_file")
    println("\nRunning script now...\n")

    include(script_file)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
