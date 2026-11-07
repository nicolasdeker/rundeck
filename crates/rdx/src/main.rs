//! `rdx` — the Rundeck-compatible server binary.
//!
//! The full CLI (`serve`, `migrate`, `check-config`, `export`, `import`, `keys`, `acl check`, `doctor`)
//! arrives in Phase 1 with its ADR. Phase 0 handles exactly one thing honestly: `--version` / `-V`
//! prints `rdx <version>` and exits 0; every other invocation prints a short usage to stderr and exits 2.
//!
//! No argument-parsing dependency yet: a dependency is added when a need justifies it (MISSION §7, §8).

#![forbid(unsafe_code)]

use std::ffi::OsString;
use std::io::Write as _;
use std::process::ExitCode;

/// Exit code for an invocation this phase does not support (usage error, as `clap` would report it).
const EXIT_USAGE: u8 = 2;

/// Usage text printed to stderr for anything other than `--version` / `-V`.
const USAGE: &str = "\
Usage: rdx --version | -V

The rdx command line (serve, migrate, check-config, export, import, keys, acl check, doctor)
arrives in Phase 1. Only `--version` / `-V` is available in this build.
";

fn main() -> ExitCode {
    let args: Vec<OsString> = std::env::args_os().skip(1).collect();
    run(&args)
}

/// Dispatches on the command-line arguments (everything after the program name).
///
/// Returns exit code 0 after printing the version, 2 after printing the usage.
fn run(args: &[OsString]) -> ExitCode {
    match args {
        [flag] if flag == "--version" || flag == "-V" => {
            let mut stdout = std::io::stdout().lock();
            // A closed stdout (e.g. `rdx -V | head -0`) is not an error worth a panic or a message.
            let _ = writeln!(stdout, "rdx {}", env!("CARGO_PKG_VERSION"));
            let _ = stdout.flush();
            ExitCode::SUCCESS
        }
        _ => {
            let mut stderr = std::io::stderr().lock();
            let _ = stderr.write_all(USAGE.as_bytes());
            let _ = stderr.flush();
            ExitCode::from(EXIT_USAGE)
        }
    }
}
