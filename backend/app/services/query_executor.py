import duckdb


class DuckDBExecutor:
    def __init__(self):
        # 使用内存模式启动 DuckDB
        self.conn = duckdb.connect(':memory:')

        # 预先塞入一些测试数据，模拟我们的业务表
        self.conn.execute("""
                          CREATE TABLE ice_data
                          (
                              year      INT,
                              region    VARCHAR,
                              thickness FLOAT
                          );
                          INSERT INTO ice_data
                          VALUES (2023, 'Barents Sea', 1.2),
                                 (2024, 'Barents Sea', 1.1),
                                 (2025, 'Barents Sea', 0.9);
                          """)

    def execute_sql(self, sql: str) -> dict:
        try:
            # 执行查询并将结果转为 Pandas DataFrame，再转为字典
            df = self.conn.execute(sql).df()
            return {"status": "success", "data": df.to_dict(orient="records")}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# 全局单例
executor = DuckDBExecutor()