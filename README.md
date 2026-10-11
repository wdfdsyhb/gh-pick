# gh-pick

**Score GitHub repos for maintenance & health before you depend on them.**

选型之前给仓库打个分：还在维护吗、社区有没有人、issue 堆没堆、license 干不干净。0-100 分，一眼看出"这个坑值不值得跳"。

## Scoring

| 维度 | 满分 | 看什么 |
|---|---|---|
| activity | 30 | 最近一次 push 距今（≤30d 满分，>2 年 0 分） |
| community | 25 | stars/forks 的对数归一 |
| issues | 20 | open issues / stars 比例（backlog 是否失控） |
| meta | 20 | 未归档 +10、有 license +10、有描述 +5、有语言 +5 |

≥80 健康可依赖；60-79 可用但自己再看看；<60 谨慎，可能弃坑。

## Usage

```bash
python gh_pick.py owner/repo
python gh_pick.py owner/repo other/repo --json out.json
python gh_pick.py https://github.com/owner/repo
```

输出：

```
wdfdsyhb/fake200                          97/100  (act 30, comm 13, iss 20, meta 20) pushed 0d ago - healthy - safe to depend on
```

## Requirements

依赖本机已安装并登录的 `gh` CLI（它负责鉴权，本工具不碰 token）：

```bash
winget install GitHub.cli && gh auth login
```

## Honest notes

- 分数是启发式：大厂官方仓库 activity 分天然高，个人项目 stars 天然吃亏——分数用来排序候选，不用来审判
- open_issues_count 包含 PR（GitHub API 的历史行为），对 issue 维度的判读略有噪声
- 零第三方依赖；对 gh 的调用只用列表参数，不经过 shell

## License

MIT
