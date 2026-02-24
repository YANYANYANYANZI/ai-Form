import sqlglot
from sqlglot import exp


class SQLReviewer:
    @staticmethod
    def is_safe(sql_query: str) -> tuple[bool, str]:
        """
        检查 SQL 是否安全。
        返回 (是否安全: bool, 错误信息/格式化后的SQL: str)
        """
        try:
            # 1. 将 SQL 解析为 AST (抽象语法树)
            # 使用 duckdb 方言解析
            parsed = sqlglot.parse_one(sql_query, read="duckdb")

            # 2. 暴力拦截：只要不是 SELECT 语句，直接拒绝！
            if not isinstance(parsed, exp.Select):
                return False, "⚠️ 拦截！只允许执行 SELECT 查询，禁止修改或删除数据。"

            # 3. 如果安全，返回标准化格式后的 SQL
            safe_sql = parsed.sql(dialect="duckdb")
            return True, safe_sql

        except sqlglot.errors.ParseError as e:
            return False, f"❌ SQL 语法错误，无法解析: {str(e)}"