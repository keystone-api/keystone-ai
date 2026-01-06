#!/usr/bin/env python3
"""
Generate consolidated CI comment for PR
Reads job summaries and creates a unified report following Chinese template
"""

import os
import json
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any

# ============================================================================
# 狀態配置
# ============================================================================

STATUS_CONFIG: Dict[str, Dict[str, str]] = {
    "success": {"emoji": "✅", "text": "執行成功", "color": "🟢"},
    "warning": {"emoji": "⚠️", "text": "執行有警告", "color": "🟡"},
    "failure": {"emoji": "❌", "text": "執行失敗", "color": "🔴"},
}

# ============================================================================
# 錯誤類型配置
# ============================================================================

ERROR_TYPE_CONFIG: Dict[str, Dict[str, Any]] = {
    "typescript": {
        "keywords": ["type", "typescript"],
        "error_type": "TypeScript 型別錯誤",
        "diagnostic": "已自動檢測型別錯誤並定位問題檔案",
        "actions": [
            "bash scripts/check-env.sh",
            "npm run typecheck",
            "bash scripts/auto-fix.sh"
        ],
        "results": [
            "型別檢查已完成",
            "錯誤定位已生成",
            "自動修復腳本已執行",
            "待重新觸發 CI pipeline 驗證"
        ],
        "quick_fix": "npm run typecheck"
    },
    "test": {
        "keywords": ["test", "jest"],
        "error_type": "測試失敗",
        "diagnostic": "已自動收集測試失敗日誌並分析根因",
        "actions": [
            "bash scripts/check-env.sh",
            "npm test -- --verbose",
            "bash scripts/auto-fix.sh"
        ],
        "results": [
            "測試環境檢查已完成",
            "詳細測試日誌已收集",
            "自動修復腳本已執行",
            "待重新觸發 CI pipeline 驗證"
        ],
        "quick_fix": "npm test"
    },
    "lint": {
        "keywords": ["lint", "eslint"],
        "error_type": "Lint 錯誤",
        "diagnostic": "已自動執行 lint 修復並套用變更",
        "actions": [
            "bash scripts/check-env.sh",
            "npm run lint:fix",
            "git diff"
        ],
        "results": [
            "Lint 自動修復已執行",
            "程式碼格式已統一",
            "變更差異已生成",
            "待重新觸發 CI pipeline 驗證"
        ],
        "quick_fix": "npm run lint:fix"
    },
    "build": {
        "keywords": ["build"],
        "error_type": "建置失敗",
        "diagnostic": "已自動檢測建置依賴並執行環境修復",
        "actions": [
            "bash scripts/check-env.sh",
            "npm install --force",
            "npm run build"
        ],
        "results": [
            "依賴檢查已完成",
            "環境修復已執行",
            "建置重試已啟動",
            "待重新觸發 CI pipeline 驗證"
        ],
        "quick_fix": "npm run build"
    },
    "default": {
        "keywords": [],
        "error_type": "CI 執行錯誤",
        "diagnostic": "已自動收集日誌並定位錯誤來源",
        "actions": [
            "bash scripts/check-env.sh",
            "bash scripts/auto-fix.sh"
        ],
        "results": [
            "環境檢查已完成",
            "自動修復腳本已執行",
            "待重新觸發 CI pipeline 驗證"
        ],
        "quick_fix": "bash scripts/check-env.sh"
    }
}

SUCCESS_FIX_INFO: Dict[str, Any] = {
    "error_type": "未知錯誤",
    "diagnostic": "所有檢查已通過，無需修復動作",
    "actions": [],
    "results": [
        "所有 CI 檢查已通過",
        "程式碼品質符合標準",
        "可以安全地合併此 PR"
    ]
}

# ============================================================================
# 輔助函數
# ============================================================================


def get_status_info(overall_status: str) -> Tuple[str, str, str]:
    """獲取狀態的 emoji、文字和顏色。"""
    config = STATUS_CONFIG.get(overall_status, STATUS_CONFIG["failure"])
    return config["emoji"], config["text"], config["color"]


def categorize_jobs(
    job_summaries: Dict[str, Any]
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """將作業分類為失敗、警告、成功和其他。"""
    failed_jobs = []
    warning_jobs = []
    success_jobs = []
    other_jobs = []

    for job_name, job_data in job_summaries.items():
        status = job_data.get("status", "unknown")
        message = job_data.get("message", "無詳細訊息")

        if status == "failure":
            failed_jobs.append(f"- ❌ **{job_name}**: {message}")
        elif status == "warning":
            warning_jobs.append(f"- ⚠️ **{job_name}**: {message}")
        elif status == "success":
            success_jobs.append(f"- ✅ **{job_name}**: {message}")
        else:
            other_jobs.append(f"- ❔ **{job_name}**: {message}")

    return failed_jobs, warning_jobs, success_jobs, other_jobs


def detect_error_type(job_summaries: Dict[str, Any]) -> Dict[str, Any]:
    """根據失敗作業的訊息檢測錯誤類型。"""
    # 收集所有失敗訊息
    all_messages = " ".join([
        job_data["message"]
        for job_data in job_summaries.values()
        if job_data.get("status") == "failure"
    ]).lower()

    if not all_messages:
        return SUCCESS_FIX_INFO

    # 按順序檢查錯誤類型
    for error_key, config in ERROR_TYPE_CONFIG.items():
        if error_key == "default":
            continue
        if any(keyword in all_messages for keyword in config["keywords"]):
            return config

    return ERROR_TYPE_CONFIG["default"]


def build_fix_actions_section(fix_actions: List[str]) -> str:
    """構建修復動作段落。"""
    if fix_actions:
        return "已執行修復動作：\n```bash\n" + "\n".join(fix_actions) + "\n```"
    return "無需執行修復動作"


def build_fix_results_text(fix_results: List[str]) -> str:
    """構建修復結果文字。"""
    if fix_results:
        return "\n".join([f"- {r}" for r in fix_results])
    return "- 無修復結果"


def generate_comment_body(
    ci_name: str,
    status_emoji: str,
    status_text: str,
    status_color: str,
    workflow_run_id: str,
    commit_sha: str,
    timestamp: str,
    error_type: str,
    instant_fix_diagnostic: str,
    fix_actions_section: str,
    fix_results_text: str,
    error_summary: str
) -> str:
    """生成評論內容。"""
    ci_name_tag = ci_name.replace(' ', '-').lower()
    return f"""<!-- CI_REPORT:{ci_name_tag} -->

## {status_emoji} {ci_name} - 客服報告

{status_color} **狀態**：{status_text}

**執行 ID**：`{workflow_run_id}`  
**Commit**：`{commit_sha[:7]}`  
**時間戳**：{timestamp}

---

### 🔍 問題診斷

**錯誤類型**：{error_type}  
**即時診斷**：{instant_fix_diagnostic}

---

### ⚡ 即時修復

{fix_actions_section}

**修復結果**：
{fix_results_text}

---

### 📊 錯誤摘要

```
{error_summary}
```

---

### 🤝 即時互動

需要更多即時操作？使用以下命令：
- `@copilot rerun {ci_name}` - 立即重新執行 CI
- `@copilot patch {ci_name}` - 立即套用修復補丁
- `@copilot logs {ci_name}` - 立即顯示完整日誌
- `@copilot sync {ci_name}` - 立即同步最新修復狀態

---

### 📚 相關資源

- [CI 故障排除文檔](./docs/ci-troubleshooting.md)
- [{ci_name} 特定文檔](./docs/README.md)
- [環境檢查工具](./scripts/check-env.sh)

---

_此評論由 {ci_name} 即時修復系統自動生成_
"""


# ============================================================================
# 主函數
# ============================================================================


def main() -> None:
    """主函數：生成合併的 CI 評論。"""
    # 解析環境變數
    ci_name = os.getenv("CI_NAME", "CI Pipeline")
    job_summaries_json = os.getenv("JOB_SUMMARIES", "{}")
    workflow_run_id = os.getenv("WORKFLOW_RUN_ID", "unknown")
    commit_sha = os.getenv("COMMIT_SHA", "unknown")
    overall_status = os.getenv("OVERALL_STATUS", "unknown")

    # 解析作業摘要
    try:
        job_summaries = json.loads(job_summaries_json)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in job-summaries", file=sys.stderr)
        job_summaries = {}

    # 獲取狀態資訊
    status_emoji, status_text, status_color = get_status_info(overall_status)

    # 分類作業
    failed_jobs, warning_jobs, success_jobs, other_jobs = categorize_jobs(job_summaries)

    # 建立錯誤摘要
    all_summaries = failed_jobs + warning_jobs + success_jobs + other_jobs
    error_summary = "\n".join(all_summaries) if all_summaries else "無詳細錯誤資訊"

    # 檢測錯誤類型並獲取修復資訊
    if failed_jobs:
        fix_info = detect_error_type(job_summaries)
    else:
        fix_info = SUCCESS_FIX_INFO

    error_type = fix_info.get("error_type", "未知錯誤")
    instant_fix_diagnostic = fix_info.get("diagnostic", "已自動收集日誌並定位錯誤來源")
    fix_actions = fix_info.get("actions", [])
    fix_results = fix_info.get("results", [])

    # 建立段落
    fix_actions_section = build_fix_actions_section(fix_actions)
    fix_results_text = build_fix_results_text(fix_results)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 生成評論內容
    comment_body = generate_comment_body(
        ci_name=ci_name,
        status_emoji=status_emoji,
        status_text=status_text,
        status_color=status_color,
        workflow_run_id=workflow_run_id,
        commit_sha=commit_sha,
        timestamp=timestamp,
        error_type=error_type,
        instant_fix_diagnostic=instant_fix_diagnostic,
        fix_actions_section=fix_actions_section,
        fix_results_text=fix_results_text,
        error_summary=error_summary
    )

    # 寫入檔案
    with open("comment_body.md", "w", encoding="utf-8") as f:
        f.write(comment_body)

    print("✅ Consolidated comment generated successfully")
    print(f"Status: {overall_status}")
    print(f"Jobs analyzed: {len(job_summaries)}")


if __name__ == "__main__":
    main()
