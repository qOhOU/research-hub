# research-hub

可扩展的科研任务入口，支持选择和组合科研 skill，以及导入和维护模块。

发行包默认不附带科研模块，目录中的来源与模块记录均为空，导入后自动建立。

将本目录放入所用 agent 的技能目录，通过 `research-hub` 调用。例如：

- “使用research-hub，精读这篇论文的方法。”
- “将这个仓库中的科研 skill 导入 hub。”

科研任务流程见 [SKILL.md](SKILL.md)，导入与目录更新见[目录维护流程](helpers/catalog-maintainer/workflow.md)。helpers 下的 workflow.md 由主入口按需读取，不作为独立技能入口。默认从仓库导入并保存到本地，再在 [catalog.json](catalog.json) 中记录名称、相对入口路径、用途和适用条件；sources 保存来源仓库及对应目录标识。

复制整个目录即可迁移。运行环境按所选模块准备，导入时保留来源附带的许可与第三方声明。

## 调用配置

导入模块保存在本目录的 modules 下，research-hub 可按确认方案使用这些模块。

默认给出 Codex 的实现方式：在每个导入技能的 `agents/openai.yaml` 中合并以下配置，保留其他已有配置。

```yaml
policy:
  allow_implicit_invocation: false
```
