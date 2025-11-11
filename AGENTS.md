# Repository Guidelines

## 项目结构与模块组织
后端代码集中在 `app/`，FastAPI 路由位于 `app/api/v1`，业务逻辑在 `controllers/` 与 `core/`，数据模型和校验分别位于 `models/` 和 `schemas/`。前端资源位于 `web/`，其中 `src/` 包含组件、路由和 Pinia store，`build/` 与 `settings/` 存放 Vite 配置。`deploy/` 提供 Docker 与示例素材，根目录的 `Makefile`、`pyproject.toml`、`run.py` 负责后端管理。新增脚本或资产请贴近现有模块，避免平行目录。

## 工作内容
当前 `web` 端仍全部依赖 mock 数据，近期目标如下：
1. 逐页梳理 `web/src` 中的业务模块，定位其 mock 依赖（包含 `mock` 目录、`api` 封装与 store），将调用替换为真正的后端接口。
2. 以既有 mock 数据结构为契约检验接口输出，发现字段或结构不一致时，直接修改后端实现（模型、序列化、控制器）以匹配前端预期，确保分页、权限与状态字段保持对齐。

## 构建、测试与开发命令
使用 `uv venv && uv add pyproject.toml` 初始化 Python 环境，随后 `make start` 或 `python run.py` 启动 API。数据库迁移依赖 Aerich：执行 `make migrate` 再 `make upgrade`。前端开发在 `web/` 目录下进行，`pnpm i` 安装依赖，`pnpm dev` 启动开发服务器，`pnpm build:pro` 生成生产构建。静态检查统一：后端使用 `make check-format`，前端使用 `pnpm lint:eslint`、`pnpm lint:style`、`pnpm lint:format`。

## 代码风格与命名规则
Python 采用 Black+isort（120 列）与 Ruff，统一 4 空格缩进，模块、异步接口、模型字段使用 snake_case。Vue/TypeScript 遵循 ESLint+Prettier 规则，组件使用 PascalCase，文件命名采用 kebab-case（如 `user-profile.vue`）。共享枚举或配置助手放入 `app/settings/` 或 `web/src/settings/`，避免重复定义。

## 测试规范
后端通过 `make test` 运行，命令会先加载 `.env` 再执行 `pytest -vv`。测试文件放在 `app/tests/`，路径需镜像业务模块（例：`app/tests/api/v1/test_roles.py`），使用 FastAPI `TestClient` 验证接口输入输出。前端至少要在 CI 中运行 `pnpm ts:check` 与各类 lint；若新增业务逻辑，请在 `web/src/__tests__/` 编写 Vitest 单测（若未建目录需先创建）或在 PR 中描述手动验证步骤。涉及安全、鉴权、持久化的模块应力求 80% 以上覆盖率。

## 提交与 Pull Request 要求
现有历史以简短祈使句为主（如 `修改包名称`），仓库同时集成 `@commitlint/config-conventional`，建议遵循 Conventional Commits（示例：`feat(core): add role seeding`）。PR 需聚焦单一主题，关联相关 Issue，并在涉及 UI 或 API 时附上截图或 cURL。说明中必须列出迁移影响、新增环境变量以及手动验证流程，方便审核者复现。

## 安全与配置提示
机密配置放入 `.env`，并在 `app/settings/config.py` 提供安全默认值；严禁在 `web/src` 明文写入凭证。新增接口时请通过 `app/core/security.py` 里的 RBAC 工具挂载权限，并同步更新 `web/src/router` 守卫以保持前后端状态一致。合并前务必执行 `docker build . -t vue-fastapi-admin` 验证镜像仍可构建，确保与已发布镜像保持一致。

## 代理协作提示
自动化代理或脚本执行命令前需确认虚拟环境已激活，可通过 `source .venv/bin/activate && make start` 快速验证。批量任务建议分阶段运行，例如：`pnpm lint:eslint && pnpm lint:style && pnpm build:pro`，再以 `pytest tests -k smoke` 进行冒烟检查。提交成果时同步附上所用命令与关键日志片段，方便后续代理复用上下文。

## 工作内容

web代码现在目前全部采用mock数据，我们的工作如下:

1. 仔细分析web端代码，把mock数据替换成后端接口数据
2. 后端接口数据需要以前端mock数据为参考，如果后端接口数据和前端mock数据不一致，需要修改后端接口代码
