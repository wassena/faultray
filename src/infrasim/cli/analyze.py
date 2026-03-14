"""Analyze and DORA report CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from infrasim.cli.main import (
    SimulationEngine,
    _print_ai_analysis,
    app,
    console,
    print_simulation_report,
)


@app.command()
def analyze(
    yaml_file: Path = typer.Argument(..., help="Infrastructure YAML file"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """AI-powered analysis with recommendations (AI analysis + recommendations)."""
    import json as json_mod

    from infrasim.ai.analyzer import InfraSimAnalyzer
    from infrasim.model.loader import load_yaml

    if not yaml_file.exists():
        console.print(f"[red]File not found: {yaml_file}[/]")
        raise typer.Exit(1)

    console.print(f"[cyan]Loading infrastructure from {yaml_file}...[/]")
    try:
        graph = load_yaml(yaml_file)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1)

    console.print(f"[cyan]Running chaos simulation ({len(graph.components)} components)...[/]")
    engine = SimulationEngine(graph)
    sim_report = engine.run_all_defaults()

    console.print("[cyan]Running AI analysis...[/]")
    ai_analyzer = InfraSimAnalyzer()
    ai_report = ai_analyzer.analyze(graph, sim_report)

    if json_output:
        import dataclasses

        report_dict = dataclasses.asdict(ai_report)
        console.print_json(json_mod.dumps(report_dict, indent=2, default=str))
    else:
        print_simulation_report(sim_report, console)
        _print_ai_analysis(ai_report, console)


@app.command()
def dora_report(
    yaml_file: Path = typer.Argument(..., help="Infrastructure YAML file"),
    output: Path = typer.Option(Path("dora-report.html"), "--output", "-o", help="Output HTML file path"),
) -> None:
    """Generate DORA compliance report (DORA compliance report generation)."""
    from infrasim.ai.analyzer import InfraSimAnalyzer
    from infrasim.model.loader import load_yaml
    from infrasim.reporter.compliance import generate_dora_report

    if not yaml_file.exists():
        console.print(f"[red]File not found: {yaml_file}[/]")
        raise typer.Exit(1)

    console.print(f"[cyan]Loading infrastructure from {yaml_file}...[/]")
    try:
        graph = load_yaml(yaml_file)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1)

    console.print(f"[cyan]Running chaos simulation ({len(graph.components)} components)...[/]")
    engine = SimulationEngine(graph)
    sim_report = engine.run_all_defaults()

    console.print("[cyan]Running AI analysis...[/]")
    ai_analyzer = InfraSimAnalyzer()
    ai_report = ai_analyzer.analyze(graph, sim_report)

    console.print("[cyan]Generating DORA compliance report...[/]")
    result_path = generate_dora_report(graph, sim_report, ai_report, output)
    console.print(f"\n[green]DORA compliance report saved to {result_path}[/]")
