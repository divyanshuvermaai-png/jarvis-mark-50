"""
J.A.R.V.I.S. Production Developer CLI Interface
Rich-powered interactive terminal console for autonomous task planning, execution, and verification.
"""
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from security import TrustLevel, kill_switch

console = Console()

def display_banner(container):
    cfg = container.config
    banner_text = Text()
    banner_text.append("J.A.R.V.I.S.  •  AUTONOMOUS AI OPERATING SYSTEM\n", style="bold cyan")
    banner_text.append(f"Architect & Owner: {cfg.owner_name}  ·  {cfg.organization}\n", style="dim white")
    banner_text.append(f"Platform: {cfg.hardware.chip} ({cfg.hardware.unified_memory_gb}GB Unified RAM)  ·  Version: {cfg.version}\n\n", style="dim cyan")
    
    # Subsystem Table
    tbl = Table(show_header=True, header_style="bold magenta", box=None)
    tbl.add_column("Subsystem", style="cyan", width=22)
    tbl.add_column("Status", width=14)
    tbl.add_column("Engine / Profile", style="white")

    # Local AI
    gemma_ready = container.router.providers.get("local_gemma_4_e2b") and container.router.providers["local_gemma_4_e2b"].is_available()
    tbl.add_row(
        "Local Intelligence",
        "[green]READY[/green]" if gemma_ready else "[yellow]OFFLINE[/yellow]",
        "Apple MLX GPU · Gemma 4 E2B 4-bit"
    )

    # Cloud AI
    gemini_ready = container.router.providers.get("google_gemini") and container.router.providers["google_gemini"].is_available()
    tbl.add_row(
        "Cloud Reasoning",
        "[green]CONNECTED[/green]" if gemini_ready else "[dim]STANDBY[/dim]",
        "Google Gemini 2.5 Flash"
    )

    # Fast Tool Orchestration
    groq_ready = container.router.providers.get("groq_cloud") and container.router.providers["groq_cloud"].is_available()
    tbl.add_row(
        "Tool Orchestration",
        "[green]CONNECTED[/green]" if groq_ready else "[dim]STANDBY[/dim]",
        "Groq Llama-3.3-70B"
    )

    # Security
    tbl.add_row(
        "Security Kernel",
        "[green]ENFORCING[/green]",
        "11-Stage Defense-in-Depth · Zero-Trust"
    )

    # Tool Registry
    tbl.add_row(
        "Tool Framework",
        f"[green]{len(container.tools.list_tools())} REGISTERED[/green]",
        ", ".join([t.id for t in container.tools.list_tools()[:3]]) + "..."
    )

    console.print(Panel(banner_text, border_style="cyan"))
    console.print(tbl)
    console.print("\n[dim]Commands: 'exit' to quit | 'kill' for emergency stop | 'tools' for tool list | 'status' for system check[/dim]\n")

def run_cli():
    from app.bootstrap import bootstrap_jarvis
    container = bootstrap_jarvis()
    display_banner(container)

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]JARVIS ❯[/bold cyan]").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                console.print("[yellow]Powering down J.A.R.V.I.S. Goodbye, Sir.[/yellow]")
                break

            if user_input.lower() == "kill":
                kill_switch.activate(actor="CLI_USER", reason="Manual operator emergency stop")
                console.print("[bold red]🚨 KILL SWITCH ACTIVATED. All tool execution halted.[/bold red]")
                continue

            if user_input.lower() == "reset":
                kill_switch.reset(actor="CLI_USER")
                console.print("[green]✅ Security lockdown reset to NORMAL.[/green]")
                continue

            if user_input.lower() == "tools":
                tbl = Table(title="Registered Tools", header_style="bold cyan")
                tbl.add_column("Tool ID", style="bold")
                tbl.add_column("Name")
                tbl.add_column("Risk Tier", style="magenta")
                tbl.add_column("Description")
                for t in container.tools.list_tools():
                    tbl.add_row(t.id, t.name, t.risk_tier.name, t.description)
                console.print(tbl)
                continue

            if user_input.lower() in ("memory", "facts"):
                count = container.semantic_memory.count()
                tbl = Table(title=f"Semantic Memory ({count} items)", header_style="bold cyan")
                tbl.add_column("Category", style="magenta")
                tbl.add_column("Content")
                tbl.add_column("Created", style="dim")
                hits = container.semantic_memory.search("*", top_k=8, mode="text") or container.semantic_memory.search("a", top_k=8, mode="vector")
                for h in hits:
                    tbl.add_row(h.get("category", "general"), h.get("content", "")[:80], h.get("created_at", "")[:19])
                console.print(tbl)
                continue

            if user_input.lower().startswith("remember "):
                fact_text = user_input[9:].strip()
                if fact_text:
                    fid = container.semantic_memory.add(fact_text, category="fact")
                    container.episodic_memory.record_episode(f"Remembered fact: {fact_text}", event_type="fact_saved")
                    console.print(f"[green]🧠 Remembered fact [dim]({fid})[/dim]:[/green] {fact_text}")
                continue

            if user_input.lower() == "procedures":
                procs = container.procedural_memory.list_procedures()
                tbl = Table(title=f"Procedural Memory Recipes ({len(procs)} available)", header_style="bold cyan")
                tbl.add_column("Name", style="bold cyan")
                tbl.add_column("Triggers", style="yellow")
                tbl.add_column("Steps", justify="right")
                tbl.add_column("Success Rate", style="green")
                for p in procs:
                    succ = p["success_count"]
                    fail = p["failure_count"]
                    rate = f"{succ}/{(succ + fail)}" if (succ + fail) > 0 else "Untested"
                    tbl.add_row(p["name"], ", ".join(p["trigger_patterns"][:3]), str(len(p["steps"])), rate)
                console.print(tbl)
                continue

            if user_input.lower() in ("episodes", "timeline"):
                eps = container.episodic_memory.get_recent_episodes(limit=8)
                tbl = Table(title="Episodic Timeline (Recent Events)", header_style="bold cyan")
                tbl.add_column("Timestamp", style="dim")
                tbl.add_column("Event Type", style="magenta")
                tbl.add_column("Summary")
                for ep in eps:
                    ts = ep["timestamp"][:19].replace("T", " ")
                    tbl.add_row(ts, ep["event_type"], ep["summary"])
                console.print(tbl)
                continue

            if user_input.lower() in ("health", "diagnostics", "checkup"):
                rep = container.diagnostics.inspect(container)
                status_color = "green" if rep.overall_status.value == "HEALTHY" else "yellow" if rep.overall_status.value == "DEGRADED" else "red"
                tbl = Table(title=f"System Diagnostics [{status_color}]{rep.overall_status.value}[/{status_color}]", header_style="bold cyan")
                tbl.add_column("Subsystem", style="bold")
                tbl.add_column("Status", style="magenta")
                tbl.add_column("Details")
                for sub_name, details in rep.subsystems.items():
                    sub_status = details.get("status", "UNKNOWN")
                    det_str = ", ".join(f"{k}: {v}" for k, v in details.items() if k != "status")
                    tbl.add_row(sub_name.title(), str(sub_status), det_str)
                tbl.add_row("Unified RAM", f"{rep.memory_usage_pct}% used", f"{rep.free_ram_gb} GB free")
                tbl.add_row("Storage Disk", "HEALTHY", f"{rep.disk_free_gb} GB free")
                console.print(tbl)
                if rep.alerts:
                    for a in rep.alerts:
                        console.print(f"[yellow]⚠️ {a}[/yellow]")
                continue

            if user_input.lower() in ("telemetry", "metrics", "stats"):
                snap = container.telemetry.get_snapshot(container)
                tbl = Table(title=f"Live System Telemetry (Uptime: {snap['uptime_seconds']}s)", header_style="bold cyan")
                tbl.add_column("Category", style="bold cyan")
                tbl.add_column("Metrics", style="yellow")
                tbl.add_column("Value", style="green")

                hw = snap["hardware"]
                tbl.add_row("Hardware", "CPU Utilization", f"{hw['cpu_percent']}% ({hw['cpu_count']} cores)")
                tbl.add_row("Hardware", "Unified Memory", f"{hw['memory']['percent']}% ({hw['memory']['used_mb']}MB / {hw['memory']['total_mb']}MB, {hw['memory']['pressure']})")
                tbl.add_row("Hardware", "Disk Headroom", f"{hw['disk']['free_gb']} GB free ({hw['disk']['percent']}% used)")
                if hw["battery"]["percent"] is not None:
                    tbl.add_row("Hardware", "Battery", f"{hw['battery']['percent']}% (Plugged: {hw['battery']['plugged']})")

                tok = snap["tokens"]
                tbl.add_row("Intelligence", "Token Throughput", f"{tok['tokens_per_sec']} tok/s (Total: {tok['total_tokens']})")
                tbl.add_row("Intelligence", "Model Queries", f"{tok['total_queries']} queries")

                lat = snap["latency"]
                tbl.add_row("Performance", "Latency (Rolling)", f"P50: {lat['p50']}ms | P95: {lat['p95']}ms | Mean: {lat['mean']}ms")

                tasks = snap["tasks"]
                tbl.add_row("Execution", "Task DAGs", f"Done: {tasks['completed']} | Active: {tasks['active']} | Fail: {tasks['failed']} ({tasks['success_rate_pct']}%)")

                sec = snap["security"]
                tbl.add_row("Security Kernel", "Status", f"KillSwitch: {'ENGAGED' if sec['kill_switch_engaged'] else 'STANDBY'} | Trust: {sec['trust_level']}")

                console.print(tbl)
                continue

            if user_input.lower().startswith("speak "):
                words = user_input[6:].strip()
                if words:
                    container.tts.speak(words, blocking=False)
                    console.print(f"[dim cyan]🔊 Dispatched speech:[/dim cyan] {words}")
                continue



            # Execute autonomous task pipeline
            with Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[cyan]{task.description}"),
                transient=True,
            ) as progress:
                p_task = progress.add_task("Planning objective...", total=None)
                
                success, response_text, task = container.orchestrator.run(
                    objective=user_input,
                    trust_level=TrustLevel.LOCAL_OWNER
                )

            # Display Execution Summary
            console.print(f"\n[bold green]Task Plan ({len(task.subtasks)} step(s)):[/bold green]")
            for st in task.subtasks:
                status_color = "green" if st.status.value == "COMPLETED" else "red"
                tool_info = f" [dim](tool: {st.tool_hint})[/dim]" if st.tool_hint else ""
                console.print(f"  • [{status_color}]{st.status.value}[/{status_color}] {st.title}{tool_info}")

            console.print("\n[bold cyan]J.A.R.V.I.S.:[/bold cyan]")
            console.print(Panel(response_text, border_style="cyan" if success else "red"))

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    run_cli()
