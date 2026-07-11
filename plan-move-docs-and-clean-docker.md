# Plan: 移动文档并清理 Docker 文件

## Summary
将 `.trae/documents/` 下的 5 个 plan 文件移动到 `7.8/agentflow/` 根目录，删除 docker 和 volumes 文件夹。

## Files to Move
| Source | Destination |
|--------|-------------|
| `.trae/documents/attu_setup_plan.md` | `7.8/agentflow/attu_setup_plan.md` |
| `.trae/documents/fix_loader_splitter_plan.md` | `7.8/agentflow/fix_loader_splitter_plan.md` |
| `.trae/documents/plan-doc-vectorize-import.md` | `7.8/agentflow/plan-doc-vectorize-import.md` |
| `.trae/documents/plan-milvus-vectorize-import.md` | `7.8/agentflow/plan-milvus-vectorize-import.md` |
| `.trae/documents/rag_pipeline_plan.md` | `7.8/agentflow/rag_pipeline_plan.md` |

## Folders to Delete
- `7.8/agentflow/docker/` - Docker 相关配置和脚本
- `7.8/agentflow/volumes/` - Docker 卷数据（minio）

## Steps
1. 移动 5 个 md 文件到 `7.8/agentflow/`
2. 删除 `docker/` 文件夹
3. 删除 `volumes/` 文件夹

## Risk Handling
- 移动文件前检查目标路径是否已存在同名文件（覆盖）
- 删除前确认文件夹内容非关键业务数据（docker/volumes 是开发环境临时数据）
