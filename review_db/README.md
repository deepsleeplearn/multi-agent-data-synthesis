# review_db

用于从 `manual_test_reviews` SQLite 中拉取前端手工测试评审记录。

当前前端评审库是轻量结构，核心字段为：

- `session_id`
- `scenario_id`
- `username`
- `status`
- `aborted_reason`
- `is_correct`
- `failed_flow_stage`
- `reviewer_notes`
- `started_at`
- `ended_at`
- `reviewed_at`
- `review_payload_json`

其中 `review_payload_json` 主要保留：

- `transcript`
- `review`
- `call_start_time`
- `collected_slots`
- `session_config.known_address`（有值时）
- 会话级元数据

不再持久化旧版本中的大块运行快照，例如：

- `scenario`
- `trace`
- `checkpoints`
- `terminal_entries`

注意：

- `session_config.known_address` 表示会话配置中的“客服已知地址”
- `collected_slots.address` 表示实际对话过程中最终收集/确认下来的地址
- 这两个字段可能一致，也可能不同，不能混用

示例：

```bash
python -m review_db.fetch_reviews outputs/frontend_manual_test.sqlite3 --limit 20
python -m review_db.fetch_reviews outputs/frontend_manual_test.sqlite3 --session-id <session_id>
python -m review_db.fetch_reviews outputs/frontend_manual_test.sqlite3 --format cli
```
