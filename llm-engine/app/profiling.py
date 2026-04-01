"""
Lightweight benchmark runner for comparing MCP mode and Text2SQL mode.
"""
import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

from test_responses import send_query

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent
MCP_SERVER_PATH = REPO_ROOT / "mcp-server" / "server.py"
DEFAULT_BENCHMARK_CSV = APP_DIR / "benchmark_questions.csv"
DEFAULT_OUTPUT_CSV = APP_DIR / "profiling_results.csv"
DEFAULT_LOG_DIR = APP_DIR / "profiling_logs"
MODE_CONFIGS = (
    {"mode": "mcp", "mcp_only": "1", "session_offset": 100000},
    {"mode": "text2sql", "mcp_only": "0", "session_offset": 200000},
)
RESULT_FIELDNAMES = [
    "mode",
    "category",
    "question",
    "session_id",
    "http_status",
    "request_success",
    "total_latency_ms",
    "response_text",
    "sql_query",
    "query_results",
    "failure_type",
    "error_detail",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark MCP vs Text2SQL and write results to CSV.")
    parser.add_argument(
        "--benchmark-csv",
        default=str(DEFAULT_BENCHMARK_CSV),
        help="CSV file containing benchmark prompts.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUTPUT_CSV),
        help="Destination CSV file for profiling results.",
    )
    parser.add_argument(
        "--summary-txt",
        default=None,
        help="Optional text file for benchmark progress and summary output.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for the benchmark app process.",
    )
    parser.add_argument(
        "--port",
        default=8000,
        type=int,
        help="Port for the benchmark app process.",
    )
    parser.add_argument(
        "--startup-timeout",
        default=60.0,
        type=float,
        help="Seconds to wait for the app to become ready.",
    )
    parser.add_argument(
        "--request-timeout",
        default=180.0,
        type=float,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--log-dir",
        default=str(DEFAULT_LOG_DIR),
        help="Directory for app and MCP server logs.",
    )
    parser.add_argument(
        "--limit",
        default=None,
        type=int,
        help="Optional number of benchmark prompts to run from the top of the CSV.",
    )
    parser.add_argument(
        "--question-limit",
        dest="limit",
        default=None,
        type=int,
        help="Optional number of benchmark questions to run from the top of the CSV.",
    )
    return parser.parse_args()


def load_benchmark_rows(csv_path: Path):
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if "question" not in (reader.fieldnames or []):
            raise ValueError(f"Benchmark CSV must contain a 'question' column: {csv_path}")

        rows = []
        for row in reader:
            question = (row.get("question") or "").strip()
            if not question:
                continue
            rows.append(
                {
                    "category": (row.get("category") or "").strip(),
                    "question": question,
                }
            )

    if not rows:
        raise ValueError(f"No benchmark prompts were found in {csv_path}")
    return rows


def open_log_file(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path.open("w", encoding="utf-8")


def log_status(handle, message: str):
    handle.write(f"{message}\n")
    handle.flush()


def start_app_process(host: str, port: int, mcp_only: str, log_dir: Path):
    env = os.environ.copy()
    env["MCP_ONLY"] = mcp_only
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    mode_name = "mcp" if mcp_only == "1" else "text2sql"
    app_log = open_log_file(log_dir / f"{mode_name}_app.log")
    return subprocess.Popen(
        command,
        cwd=str(APP_DIR),
        env=env,
        stdout=app_log,
        stderr=app_log,
    ), app_log


def start_mcp_server_process(log_dir: Path):
    command = [sys.executable, str(MCP_SERVER_PATH)]
    mcp_log = open_log_file(log_dir / "mcp_server.log")
    return subprocess.Popen(
        command,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
        stdout=mcp_log,
        stderr=mcp_log,
    ), mcp_log


def wait_for_app_ready(base_url: str, timeout_seconds: float, process: subprocess.Popen):
    deadline = time.time() + timeout_seconds
    ready_url = f"{base_url}/docs"
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Benchmark app exited early with code {process.returncode}")
        try:
            response = requests.get(ready_url, timeout=2)
            if response.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for benchmark app to become ready at {ready_url}")


def stop_app_process(process: subprocess.Popen):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def stop_processes(processes):
    for process in reversed(processes):
        stop_app_process(process)


def close_log_files(log_files):
    for log_file in log_files:
        try:
            log_file.close()
        except Exception:
            pass


def normalize_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def extract_error_detail(response_json, fallback_text=""):
    if isinstance(response_json, dict):
        detail = response_json.get("detail")
        if isinstance(detail, dict):
            return normalize_text(detail.get("error") or detail)
        if detail is not None:
            return normalize_text(detail)
    return normalize_text(fallback_text)


def classify_failure(http_status, response_json, response_text):
    if http_status is None:
        return "exception"
    if http_status >= 400:
        error_text = extract_error_detail(response_json, response_text).lower()
        if "database error" in error_text or "sql error" in error_text:
            return "db_error"
        if "tool error" in error_text or "mcp" in error_text:
            return "tool_error"
        return "http_error"

    if isinstance(response_json, dict):
        response_value = normalize_text(response_json.get("response")).strip()
        sql_query = normalize_text(response_json.get("sql_query")).strip()
        query_results = normalize_text(response_json.get("query_results")).strip()
        if not response_value and not sql_query and not query_results:
            return "empty_response"
        combined_text = " ".join([response_value.lower(), query_results.lower()])
        if "database error" in combined_text:
            return "db_error"
        if "tool error" in combined_text:
            return "tool_error"

    return "none"


def build_result_row(mode: str, benchmark_row: dict, session_id: int, result: dict):
    response_json = result.get("json")
    response_text = ""
    sql_query = ""
    query_results = ""
    total_latency_ms = ""

    if isinstance(response_json, dict):
        response_text = normalize_text(response_json.get("response"))
        sql_query = normalize_text(response_json.get("sql_query"))
        query_results = normalize_text(response_json.get("query_results"))
        profiling_payload = response_json.get("profiling") or {}
        total_latency_ms = profiling_payload.get("total_latency_ms", "")

    failure_type = classify_failure(result.get("status_code"), response_json, result.get("text", ""))
    error_detail = ""
    if failure_type != "none":
        error_detail = extract_error_detail(response_json, result.get("error", result.get("text", "")))

    return {
        "mode": mode,
        "category": benchmark_row.get("category", ""),
        "question": benchmark_row["question"],
        "session_id": session_id,
        "http_status": result.get("status_code", ""),
        "request_success": failure_type == "none",
        "total_latency_ms": total_latency_ms,
        "response_text": response_text,
        "sql_query": sql_query,
        "query_results": query_results,
        "failure_type": failure_type,
        "error_detail": error_detail,
    }


def run_mode(base_url: str, host: str, port: int, benchmark_rows, mode_config: dict, startup_timeout: float, request_timeout: float, log_dir: Path, summary_handle):
    log_status(summary_handle, f"Running benchmark mode: {mode_config['mode']}")
    processes = []
    log_files = []
    if mode_config["mcp_only"] == "1":
        mcp_process, mcp_log = start_mcp_server_process(log_dir)
        processes.append(mcp_process)
        log_files.append(mcp_log)
        time.sleep(1)
    process, app_log = start_app_process(host, port, mode_config["mcp_only"], log_dir)
    processes.append(process)
    log_files.append(app_log)
    results = []
    try:
        wait_for_app_ready(base_url, startup_timeout, process)
        query_url = f"{base_url}/query"
        for index, benchmark_row in enumerate(benchmark_rows, start=1):
            session_id = mode_config["session_offset"] + index
            log_status(
                summary_handle,
                f"[{mode_config['mode']}] Prompt {index}/{len(benchmark_rows)}: {benchmark_row['question']}",
            )
            try:
                response_result = send_query(
                    benchmark_row["question"],
                    session_id,
                    url=query_url,
                    timeout=request_timeout,
                )
            except requests.RequestException as exc:
                response_result = {
                    "status_code": None,
                    "ok": False,
                    "json": None,
                    "text": "",
                    "error": str(exc),
                }
            results.append(build_result_row(mode_config["mode"], benchmark_row, session_id, response_result))
    finally:
        stop_processes(processes)
        close_log_files(log_files)
    return results


def write_results_csv(output_path: Path, rows):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary_path: Path, output_path: Path, rows, benchmark_csv: Path, log_dir: Path):
    success_count = sum(1 for row in rows if row["failure_type"] == "none")
    failure_count = len(rows) - success_count
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write(f"Wrote {len(rows)} profiling rows to {output_path}\n")
        handle.write(f"Successful rows: {success_count}\n")
        handle.write(f"Failed rows: {failure_count}\n")
        handle.write(f"Benchmark CSV: {benchmark_csv}\n")
        handle.write(f"Log directory: {log_dir}\n")


def main():
    args = parse_args()
    benchmark_csv = Path(args.benchmark_csv).resolve()
    output_csv = Path(args.output_csv).resolve()
    if args.summary_txt:
        summary_txt = Path(args.summary_txt).resolve()
    else:
        summary_txt = output_csv.with_suffix(".txt")
    log_dir = Path(args.log_dir).resolve()
    base_url = f"http://{args.host}:{args.port}"
    benchmark_rows = load_benchmark_rows(benchmark_csv)
    if args.limit is not None:
        benchmark_rows = benchmark_rows[:args.limit]

    all_results = []
    summary_txt.parent.mkdir(parents=True, exist_ok=True)
    with summary_txt.open("w", encoding="utf-8") as summary_handle:
        log_status(summary_handle, f"Benchmark CSV: {benchmark_csv}")
        log_status(summary_handle, f"Output CSV: {output_csv}")
        log_status(summary_handle, f"Log directory: {log_dir}")
        for mode_config in MODE_CONFIGS:
            mode_results = run_mode(
                base_url=base_url,
                host=args.host,
                port=args.port,
                benchmark_rows=benchmark_rows,
                mode_config=mode_config,
                startup_timeout=args.startup_timeout,
                request_timeout=args.request_timeout,
                log_dir=log_dir,
                summary_handle=summary_handle,
            )
            all_results.extend(mode_results)

    write_results_csv(output_csv, all_results)
    write_summary(summary_txt, output_csv, all_results, benchmark_csv, log_dir)


if __name__ == "__main__":
    main()
