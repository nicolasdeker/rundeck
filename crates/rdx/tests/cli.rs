//! Black-box tests of the `rdx` binary built by Cargo (`CARGO_BIN_EXE_rdx`).

use std::error::Error;
use std::process::{Command, Output};

type TestResult = Result<(), Box<dyn Error>>;

fn rdx(args: &[&str]) -> Result<Output, Box<dyn Error>> {
    Ok(Command::new(env!("CARGO_BIN_EXE_rdx"))
        .args(args)
        .output()?)
}

#[test]
fn version_long_flag_prints_name_and_version_and_exits_zero() -> TestResult {
    let output = rdx(&["--version"])?;
    assert_eq!(output.status.code(), Some(0));
    assert_eq!(
        String::from_utf8(output.stdout)?,
        format!("rdx {}\n", env!("CARGO_PKG_VERSION"))
    );
    assert!(
        output.stderr.is_empty(),
        "stderr must stay empty on --version"
    );
    Ok(())
}

#[test]
fn version_short_flag_matches_long_flag() -> TestResult {
    let short = rdx(&["-V"])?;
    let long = rdx(&["--version"])?;
    assert_eq!(short.status.code(), Some(0));
    assert_eq!(short.stdout, long.stdout);
    Ok(())
}

#[test]
fn unknown_command_prints_usage_to_stderr_and_exits_two() -> TestResult {
    let output = rdx(&["serve"])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty(), "usage goes to stderr, not stdout");
    let stderr = String::from_utf8(output.stderr)?;
    assert!(
        stderr.starts_with("Usage: rdx"),
        "unexpected usage text: {stderr}"
    );
    assert!(
        stderr.contains("Phase 1"),
        "usage must say the CLI arrives in Phase 1: {stderr}"
    );
    Ok(())
}

#[test]
fn no_arguments_is_a_usage_error() -> TestResult {
    let output = rdx(&[])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    Ok(())
}

#[test]
fn version_with_extra_arguments_is_a_usage_error() -> TestResult {
    let output = rdx(&["--version", "extra"])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    Ok(())
}
