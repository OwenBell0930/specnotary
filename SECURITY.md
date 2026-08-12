# Security Policy

## 范围

SpecAnvil 是本地 CLI：读取 YAML/JSON/Markdown/HTML，写 Markdown。它不发起网络请求、不执行被检查的文件内容、不上传任何数据。

## 报告漏洞

若发现安全问题（例如构造的 YAML/HTML 导致任意代码执行或路径逃逸），请通过 GitHub Issues 以最小复现描述报告；若涉及可被利用的细节，请在 Issue 中说明并等待维护者提供私下渠道后再提交 PoC。

- 使用 `yaml.safe_load`（禁止任意对象反序列化）是硬约束，任何改动不得放宽。
- 校验过程只读被检查文件；除显式输出路径外不得写入任何文件。

## 支持版本

只支持最新 minor 版本（当前 0.2.x）。
