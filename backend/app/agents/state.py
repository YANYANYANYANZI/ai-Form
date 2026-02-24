from typing import TypedDict, Dict, Any, List

class AgentState(TypedDict):
    user_query: str
    knowledge_context: str    # 新增：RAG 知识库上下文
    intent: str               # 意图：'analyze', 'edit_table', 'qa'
    sheet_updates: List[Dict[str, Any]]
    sql_query: str
    sql_result: Dict[str, Any]
    bi_json: Dict[str, Any]
    answer: str               # 新增：知识库问答的直接回复
    error: str