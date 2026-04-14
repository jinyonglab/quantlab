# 贡献指南

感谢您对 InvestLab 项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过 [GitHub Issues](https://github.com/yourusername/InvestLab/issues) 提交：

1. 使用清晰的标题描述问题
2. 提供详细的复现步骤
3. 说明期望行为和实际行为
4. 提供环境信息（操作系统、Python版本等）
5. 如有错误日志，请一并附上

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/yourusername/InvestLab.git
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **编写代码**
   - 遵循 PEP 8 代码规范
   - 添加必要的注释
   - 更新相关文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new strategy"
   ```

5. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: add MACD strategy support
fix: correct calculation of Sharpe ratio
docs: update README with new examples
```

## 🧪 测试

提交 PR 前请确保：

1. 代码可以正常运行
2. 没有引入新的 bug
3. 更新了相关文档

## 📋 代码规范

- 使用 4 空格缩进
- 最大行长度 100 字符
- 使用有意义的变量名
- 添加 docstring 说明函数功能

## 💡 策略贡献

如果您想贡献新的交易策略：

1. 在 `strategies/` 目录下创建策略文件
2. 继承基类并实现必要方法
3. 在 `strategies/__init__.py` 中注册策略
4. 提供策略说明文档

## 📞 联系方式

如有疑问，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至 [your-email@example.com]

再次感谢您的贡献！
