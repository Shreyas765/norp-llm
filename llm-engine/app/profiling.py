"""
Improved benchmark runner for comparing MCP mode and Text2SQL mode.
"""
import argparse
import csv
import json
import math
import os
import re
import statistics
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
DEFAULT_VALIDATION_JSON = APP_DIR / "benchmark_validations.json"
DEFAULT_OUTPUT_CSV = APP_DIR / "profiling_results.csv"
DEFAULT_LOG_DIR = APP_DIR / "profiling_logs"
MODE_CONFIGS = (
    {"mode": "mcp", "mcp_only": "1", "session_offset": 100000},
    {"mode": "text2sql", "mcp_only": "0", "session_offset": 200000},
)
RESULT_FIELDNAMES = [
    "run_id",
    "question_id",
    "mode",
    "category",
    "question",
    "session_id",
    "http_status",
    "request_success",
    "validated_success",
    "validation_status",
    "assertion_type",
    "assertion_detail",
    "failure_type",
    "error_detail",
    "client_request_latency_ms",
    "server_handler_latency_ms",
    "app_startup_latency_ms",
    "mcp_server_startup_latency_ms",
    "sql_execution_latency_ms",
    "final_llm_response",
    "response_text",
    "sql_query",
    "query_results",
    "sql_execution_success",
    "sql_execution_error",
    "model_name",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "estimated_cost_usd",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark MCP vs Text2SQL and write results to CSV.")
    parser.add_argument(
        "--benchmark-csv",
        default=str(DEFAULT_BENCHMARK_CSV),
        help="CSV file containing benchmark prompts.",
    )
    parser.add_argument(
        "--validation-json",
        default=str(DEFAULT_VALIDATION_JSON),
        help="JSON file containing validation rules keyed by question_id.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUTPUT_CSV),
        help="Base destination CSV file for profiling results.",
    )
    parser.add_argument(
        "--summary-txt",
        default=None,
        help="Optional base text file for benchmark progress and summary output.",
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
        help="Base directory for app and MCP server logs.",
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


def create_run_id():
    return time.strftime("%Y%m%d_%H%M%S")


def build_versioned_path(base_path: Path, run_id: str) -> Path:
    return base_path.with_name(f"{base_path.stem}_{run_id}{base_path.suffix}")


def load_benchmark_rows(csv_path: Path):
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"question_id", "category", "question"}
        missing_columns = required_columns.difference(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Benchmark CSV is missing required columns: {', '.join(sorted(missing_columns))}")

        rows = []
        seen_question_ids = set()
        for row in reader:
            question_id = (row.get("question_id") or "").strip()
            question = (row.get("question") or "").strip()
            if not question_id or not question:
                continue
            if question_id in seen_question_ids:
                raise ValueError(f"Duplicate question_id in benchmark CSV: {question_id}")
            seen_question_ids.add(question_id)
            rows.append(
                {
                    "question_id": question_id,
                    "category": (row.get("category") or "").strip(),
                    "question": question,
                }
            )

    if not rows:
        raise ValueError(f"No benchmark prompts were found in {csv_path}")
    return rows


def load_validation_rules(validation_path: Path):
    with validation_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Validation JSON must be an object keyed by question_id.")
    return data


def resolve_validation_rule(question_id: str, validation_rules: dict, mode: str):
    rule = validation_rules.get(question_id)
    if not isinstance(rule, dict):
        return None

    if "shared" in rule or mode in rule:
        merged = {}
        shared_rule = rule.get("shared", {})
        mode_rule = rule.get(mode, {})
        if isinstance(shared_rule, dict):
            merged.update(shared_rule)
        if isinstance(mode_rule, dict):
            merged.update(mode_rule)
        return merged or None

    return rule


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
    start_time = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=str(APP_DIR),
        env=env,
        stdout=app_log,
        stderr=app_log,
    )
    return process, app_log, start_time


def start_mcp_server_process(log_dir: Path):
    command = [sys.executable, str(MCP_SERVER_PATH)]
    mcp_log = open_log_file(log_dir / "mcp_server.log")
    start_time = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
        stdout=mcp_log,
        stderr=mcp_log,
    )
    return process, mcp_log, start_time


def wait_for_mcp_server_ready(process: subprocess.Popen, start_time: float):
    time.sleep(1)
    if process.poll() is not None:
        raise RuntimeError(f"MCP server exited early with code {process.returncode}")
    return round((time.perf_counter() - start_time) * 1000, 3)


def wait_for_app_ready(base_url: str, timeout_seconds: float, process: subprocess.Popen, start_time: float):
    deadline = time.time() + timeout_seconds
    ready_url = f"{base_url}/docs"
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Benchmark app exited early with code {process.returncode}")
        try:
            response = requests.get(ready_url, timeout=2)
            if response.ok:
                return round((time.perf_counter() - start_time) * 1000, 3)
        except requests.RequestException:
            pass
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for benchmark app to become ready at {ready_url}")


def stop_process(process: subprocess.Popen):
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
        stop_process(process)


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
        if response_json.get("sql_execution_error") is not None:
            return normalize_text(response_json.get("sql_execution_error"))
    return normalize_text(fallback_text)


def safe_float(value):
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percentile(values, pct: float):
    if not values:
        return None
    sorted_values = sorted(values)
    index = max(0, min(len(sorted_values) - 1, math.ceil((pct / 100) * len(sorted_values)) - 1))
    return sorted_values[index]


def get_validated_text(mode: str, response_json):
    if not isinstance(response_json, dict):
        return ""
    if mode == "mcp":
        return normalize_text(response_json.get("response"))
    return normalize_text(response_json.get("query_results"))


def validate_text_against_rule(target_text: str, rule: dict):
    assertion_type = rule.get("assertion_type", "nonempty")
    normalized_text = target_text if rule.get("case_sensitive") else target_text.lower()
    expected_values = rule.get("expected_substrings", []) or []
    expected_values = expected_values if rule.get("case_sensitive") else [value.lower() for value in expected_values]

    if assertion_type == "contains_all":
        missing = [value for value in expected_values if value not in normalized_text]
        if missing:
            return False, assertion_type, f"Missing expected substrings: {', '.join(missing)}"
        return True, assertion_type, f"Matched all expected substrings: {', '.join(expected_values)}"

    if assertion_type == "contains_any":
        for value in expected_values:
            if value in normalized_text:
                return True, assertion_type, f"Matched expected substring: {value}"
        return False, assertion_type, f"None of the expected substrings were found: {', '.join(expected_values)}"

    if assertion_type == "regex":
        pattern = rule.get("regex_pattern", "")
        if not pattern:
            return False, assertion_type, "Validation rule is missing regex_pattern."
        flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
        if re.search(pattern, target_text, flags=flags):
            return True, assertion_type, f"Matched regex pattern: {pattern}"
        return False, assertion_type, f"Did not match regex pattern: {pattern}"

    if assertion_type == "nonempty":
        if target_text.strip():
            return True, assertion_type, "Validated target is non-empty."
        return False, assertion_type, "Validated target is empty."

    return False, assertion_type, f"Unsupported assertion_type: {assertion_type}"


def validate_result(mode: str, response_result: dict, validation_rule: dict):
    response_json = response_result.get("json")

    if response_result.get("status_code") is None:
        return False, "transport_failure", "transport_failure", normalize_text(
            response_result.get("error", "Request failed before response.")
        )

    if response_result.get("status_code", 0) >= 400:
        return False, "http_failure", "http_failure", extract_error_detail(response_json, response_result.get("text", ""))

    if validation_rule is None:
        return False, "missing_validation_rule", "missing_validation_rule", "No validation rule found for question_id."

    if mode == "text2sql":
        sql_execution_success = response_json.get("sql_execution_success") if isinstance(response_json, dict) else None
        if sql_execution_success is not True:
            return (
                False,
                "sql_execution_failed",
                validation_rule.get("assertion_type", ""),
                normalize_text(response_json.get("sql_execution_error")) if isinstance(response_json, dict) else "SQL execution did not succeed.",
            )

    validated_text = get_validated_text(mode, response_json)
    if not validated_text.strip():
        return (
            False,
            "missing_validated_text",
            validation_rule.get("assertion_type", ""),
            "Expected validated text was empty.",
        )

    matched, assertion_type, assertion_detail = validate_text_against_rule(validated_text, validation_rule)
    return matched, ("validated" if matched else "assertion_failed"), assertion_type, assertion_detail


def classify_failure(mode: str, result_row: dict):
    http_status = result_row["http_status"]
    if http_status == "":
        return "exception"
    if safe_float(http_status) is not None and int(float(http_status)) >= 400:
        error_text = normalize_text(result_row["error_detail"]).lower()
        if "database error" in error_text or "sql error" in error_text:
            return "db_error"
        if "tool error" in error_text or "mcp" in error_text:
            return "tool_error"
        return "http_error"

    if mode == "text2sql" and result_row["sql_execution_success"] is False:
        return "sql_error"

    if result_row["validated_success"] is False:
        return "validation_failed"

    return "none"


def estimate_cost_usd(model_name, prompt_tokens, completion_tokens):
    input_price = safe_float(os.getenv("PROFILER_INPUT_COST_PER_1M_TOKENS"))
    output_price = safe_float(os.getenv("PROFILER_OUTPUT_COST_PER_1M_TOKENS"))
    if input_price is None or output_price is None:
        return None
    if prompt_tokens is None or completion_tokens is None:
        return None

    input_cost = (prompt_tokens / 1_000_000) * input_price
    output_cost = (completion_tokens / 1_000_000) * output_price
    return round(input_cost + output_cost, 8)


def build_result_row(
    run_id: str,
    mode: str,
    benchmark_row: dict,
    validation_rule: dict,
    session_id: int,
    response_result: dict,
    client_latency_ms: float,
    app_startup_latency_ms: float,
    mcp_server_startup_latency_ms,
):
    response_json = response_result.get("json") if isinstance(response_result.get("json"), dict) else {}
    profiling_payload = response_json.get("profiling", {}) if isinstance(response_json, dict) else {}
    server_handler_latency_ms = safe_float(profiling_payload.get("server_handler_latency_ms"))
    sql_execution_latency_ms = safe_float(profiling_payload.get("sql_execution_latency_ms"))
    prompt_tokens = profiling_payload.get("prompt_tokens")
    completion_tokens = profiling_payload.get("completion_tokens")
    total_tokens = profiling_payload.get("total_tokens")
    model_name = profiling_payload.get("model_name")
    estimated_cost_usd = estimate_cost_usd(model_name, prompt_tokens, completion_tokens)

    validated_success, validation_status, assertion_type, assertion_detail = validate_result(
        mode,
        response_result,
        validation_rule,
    )

    row = {
        "run_id": run_id,
        "question_id": benchmark_row["question_id"],
        "mode": mode,
        "category": benchmark_row.get("category", ""),
        "question": benchmark_row["question"],
        "session_id": session_id,
        "http_status": response_result.get("status_code", ""),
        "request_success": response_result.get("status_code") is not None and response_result.get("status_code", 0) < 400,
        "validated_success": validated_success,
        "validation_status": validation_status,
        "assertion_type": assertion_type,
        "assertion_detail": assertion_detail,
        "failure_type": "",
        "error_detail": "",
        "client_request_latency_ms": round(client_latency_ms, 3),
        "server_handler_latency_ms": server_handler_latency_ms,
        "app_startup_latency_ms": app_startup_latency_ms,
        "mcp_server_startup_latency_ms": mcp_server_startup_latency_ms,
        "sql_execution_latency_ms": sql_execution_latency_ms,
        "final_llm_response": normalize_text(response_json.get("final_llm_response")),
        "response_text": normalize_text(response_json.get("response")),
        "sql_query": normalize_text(response_json.get("sql_query")),
        "query_results": normalize_text(response_json.get("query_results")),
        "sql_execution_success": response_json.get("sql_execution_success"),
        "sql_execution_error": normalize_text(response_json.get("sql_execution_error")),
        "model_name": normalize_text(model_name),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost_usd,
    }
    row["failure_type"] = classify_failure(mode, row)
    if row["failure_type"] != "none":
        if row["failure_type"] == "validation_failed":
            row["error_detail"] = row["assertion_detail"]
        else:
            row["error_detail"] = extract_error_detail(
                response_json,
                response_result.get("error", response_result.get("text", "")),
            )
    return row


def run_mode(
    run_id: str,
    base_url: str,
    host: str,
    port: int,
    benchmark_rows,
    validation_rules: dict,
    mode_config: dict,
    startup_timeout: float,
    request_timeout: float,
    log_dir: Path,
    summary_handle,
):
    log_status(summary_handle, f"Running benchmark mode: {mode_config['mode']}")
    processes = []
    log_files = []
    mcp_server_startup_latency_ms = None

    if mode_config["mcp_only"] == "1":
        mcp_process, mcp_log, mcp_start_time = start_mcp_server_process(log_dir)
        processes.append(mcp_process)
        log_files.append(mcp_log)
        mcp_server_startup_latency_ms = wait_for_mcp_server_ready(mcp_process, mcp_start_time)

    process, app_log, app_start_time = start_app_process(host, port, mode_config["mcp_only"], log_dir)
    processes.append(process)
    log_files.append(app_log)
    app_startup_latency_ms = None
    results = []
    try:
        app_startup_latency_ms = wait_for_app_ready(base_url, startup_timeout, process, app_start_time)
        query_url = f"{base_url}/query"
        for index, benchmark_row in enumerate(benchmark_rows, start=1):
            session_id = mode_config["session_offset"] + index
            log_status(
                summary_handle,
                f"[{mode_config['mode']}] Prompt {index}/{len(benchmark_rows)}: {benchmark_row['question_id']} - {benchmark_row['question']}",
            )
            client_start = time.perf_counter()
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
            client_latency_ms = (time.perf_counter() - client_start) * 1000
            validation_rule = resolve_validation_rule(
                benchmark_row["question_id"],
                validation_rules,
                mode_config["mode"],
            )
            results.append(
                build_result_row(
                    run_id=run_id,
                    mode=mode_config["mode"],
                    benchmark_row=benchmark_row,
                    validation_rule=validation_rule,
                    session_id=session_id,
                    response_result=response_result,
                    client_latency_ms=client_latency_ms,
                    app_startup_latency_ms=app_startup_latency_ms,
                    mcp_server_startup_latency_ms=mcp_server_startup_latency_ms,
                )
            )
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


def summarize_rows(rows, summary_path: Path, run_id: str, benchmark_csv: Path, validation_json: Path, log_dir: Path, output_csv: Path):
    by_mode = {}
    for row in rows:
        by_mode.setdefault(row["mode"], []).append(row)

    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write(f"Run ID: {run_id}\n")
        handle.write(f"Benchmark CSV: {benchmark_csv}\n")
        handle.write(f"Validation JSON: {validation_json}\n")
        handle.write(f"Output CSV: {output_csv}\n")
        handle.write(f"Log directory: {log_dir}\n")
        handle.write(f"Total rows: {len(rows)}\n\n")

        for mode in sorted(by_mode):
            mode_rows = by_mode[mode]
            validated_success_count = sum(1 for row in mode_rows if row["validated_success"] is True)
            transport_failure_count = sum(1 for row in mode_rows if row["failure_type"] in {"exception", "http_error", "tool_error", "db_error", "sql_error"})
            handle.write(f"[Mode: {mode}]\n")
            handle.write(f"Rows: {len(mode_rows)}\n")
            handle.write(f"Validated success count: {validated_success_count}\n")
            handle.write(f"Validated success rate: {round((validated_success_count / len(mode_rows)) * 100, 2) if mode_rows else 0}%\n")
            handle.write(f"Transport/system failure count: {transport_failure_count}\n")
            handle.write(f"Transport/system failure rate: {round((transport_failure_count / len(mode_rows)) * 100, 2) if mode_rows else 0}%\n")

            for field_name, label in (
                ("client_request_latency_ms", "Client latency"),
                ("server_handler_latency_ms", "Server latency"),
            ):
                values = [safe_float(row[field_name]) for row in mode_rows]
                values = [value for value in values if value is not None]
                if values:
                    handle.write(f"{label} avg/median/p95: {round(statistics.mean(values), 3)} / {round(statistics.median(values), 3)} / {round(percentile(values, 95), 3)} ms\n")
                else:
                    handle.write(f"{label} avg/median/p95: unavailable\n")

            token_values = [safe_float(row["total_tokens"]) for row in mode_rows]
            token_values = [value for value in token_values if value is not None]
            cost_values = [safe_float(row["estimated_cost_usd"]) for row in mode_rows]
            cost_values = [value for value in cost_values if value is not None]
            if token_values:
                handle.write(f"Total tokens: {int(sum(token_values))}\n")
                handle.write(f"Average tokens/request: {round(statistics.mean(token_values), 3)}\n")
            else:
                handle.write("Total tokens: unavailable\n")
                handle.write("Average tokens/request: unavailable\n")
            if cost_values:
                handle.write(f"Total estimated cost (USD): {round(sum(cost_values), 8)}\n")
                handle.write(f"Average estimated cost/request (USD): {round(statistics.mean(cost_values), 8)}\n")
            else:
                handle.write("Total estimated cost (USD): unavailable\n")
                handle.write("Average estimated cost/request (USD): unavailable\n")

            handle.write("Per-category breakdown:\n")
            categories = sorted({row["category"] for row in mode_rows})
            for category in categories:
                category_rows = [row for row in mode_rows if row["category"] == category]
                validated_category_count = sum(1 for row in category_rows if row["validated_success"] is True)
                failure_category_count = sum(1 for row in category_rows if row["failure_type"] != "none")
                client_values = [safe_float(row["client_request_latency_ms"]) for row in category_rows]
                client_values = [value for value in client_values if value is not None]
                avg_client = round(statistics.mean(client_values), 3) if client_values else "unavailable"
                p95_client = round(percentile(client_values, 95), 3) if client_values else "unavailable"
                handle.write(
                    f"- {category}: rows={len(category_rows)}, validated_success_rate={round((validated_category_count / len(category_rows)) * 100, 2) if category_rows else 0}%, failure_rate={round((failure_category_count / len(category_rows)) * 100, 2) if category_rows else 0}%, avg_client_latency_ms={avg_client}, p95_client_latency_ms={p95_client}\n"
                )
            handle.write("\n")

        if not os.getenv("PROFILER_INPUT_COST_PER_1M_TOKENS") or not os.getenv("PROFILER_OUTPUT_COST_PER_1M_TOKENS"):
            handle.write("Estimated cost was unavailable because PROFILER_INPUT_COST_PER_1M_TOKENS and PROFILER_OUTPUT_COST_PER_1M_TOKENS were not both set.\n")


def main():
    args = parse_args()
    run_id = create_run_id()
    benchmark_csv = Path(args.benchmark_csv).resolve()
    validation_json = Path(args.validation_json).resolve()
    output_csv_base = Path(args.output_csv).resolve()
    output_csv = build_versioned_path(output_csv_base, run_id)

    if args.summary_txt:
        summary_txt_base = Path(args.summary_txt).resolve()
    else:
        summary_txt_base = output_csv_base.with_suffix(".txt")
    summary_txt = build_versioned_path(summary_txt_base, run_id)

    log_dir_base = Path(args.log_dir).resolve()
    log_dir = log_dir_base / run_id
    base_url = f"http://{args.host}:{args.port}"

    benchmark_rows = load_benchmark_rows(benchmark_csv)
    if args.limit is not None:
        benchmark_rows = benchmark_rows[:args.limit]
    validation_rules = load_validation_rules(validation_json)

    summary_txt.parent.mkdir(parents=True, exist_ok=True)
    with summary_txt.open("w", encoding="utf-8") as summary_handle:
        log_status(summary_handle, f"Run ID: {run_id}")
        log_status(summary_handle, f"Benchmark CSV: {benchmark_csv}")
        log_status(summary_handle, f"Validation JSON: {validation_json}")
        log_status(summary_handle, f"Output CSV: {output_csv}")
        log_status(summary_handle, f"Log directory: {log_dir}")
        all_results = []
        for mode_config in MODE_CONFIGS:
            mode_results = run_mode(
                run_id=run_id,
                base_url=base_url,
                host=args.host,
                port=args.port,
                benchmark_rows=benchmark_rows,
                validation_rules=validation_rules,
                mode_config=mode_config,
                startup_timeout=args.startup_timeout,
                request_timeout=args.request_timeout,
                log_dir=log_dir,
                summary_handle=summary_handle,
            )
            all_results.extend(mode_results)

    write_results_csv(output_csv, all_results)
    summarize_rows(all_results, summary_txt, run_id, benchmark_csv, validation_json, log_dir, output_csv)


if __name__ == "__main__":
    main()
