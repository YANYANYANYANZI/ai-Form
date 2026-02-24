from backend.app.agents.state import AgentState
from backend.app.agents.reviewer import SQLReviewer
from backend.app.services.query_executor import executor
from backend.app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

llm = ChatOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.OPENAI_API_BASE, model="deepseek-chat",
                 temperature=0.1)


def planner_node(state: AgentState) -> AgentState:
    print("🧠 [Planner] 正在分析用户意图...")
    query = state.get("user_query", "")
    context = state.get("knowledge_context", "")  # 提取外挂知识

    system_prompt = f"""你是一个企业级智能分析助手。你有三种能力，请根据用户意图选择输出对应的 JSON 格式：

    【能力1：分析与画图】(如果用户想查数据、对比、画图)
    输出: {{"intent": "analyze", "sql": "SELECT region, thickness FROM ice_data;"}}

    【能力2：修改表格数据】(如果用户要求新增、修改、填入数据)
    输出: {{"intent": "edit_table", "updates": [{{"r": 2, "c": 0, "v": "2025"}}]}}

    【能力3：知识库问答】(如果用户提问内容与以下知识库相关，或者是日常聊天)
    [外挂知识库]: {context}
    输出: {{"intent": "qa", "answer": "结合知识库给出的详细回答"}}

    【严厉警告】：必须且只能输出纯 JSON！绝不要输出 Markdown 标记！"""

    json_str = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)]).content.replace(
        "```json", "").replace("```", "").strip()

    try:
        result = json.loads(json_str)
        intent = result.get("intent", "analyze")
        if intent == "edit_table":
            return {"intent": intent, "sheet_updates": result.get("updates", [])}
        elif intent == "qa":
            return {"intent": intent, "answer": result.get("answer", "")}  # 触发问答
        else:
            return {"intent": intent, "sql_query": result.get("sql", "")}
    except Exception as e:
        return {"error": "JSON解析失败"}


def reviewer_and_execute_node(state: AgentState) -> AgentState:
    if state.get("intent") in ["edit_table", "qa"]: return state  # 非 SQL 意图直接放行
    is_safe, result = SQLReviewer.is_safe(state.get("sql_query", ""))
    if not is_safe: return {"error": result}
    return {"sql_result": executor.execute_sql(result)}


def bi_render_node(state: AgentState) -> AgentState:
    if state.get("intent") in ["edit_table", "qa"]: return state
    data = state.get("sql_result", {}).get("data", [])
    system_prompt = f"请将数据: {json.dumps(data, ensure_ascii=False)} 转换为 ECharts 'option' JSON 对象。只能输出纯 JSON！"
    try:
        return {"bi_json": json.loads(
            llm.invoke([SystemMessage(content=system_prompt)]).content.replace("```json", "").replace("```",
                                                                                                      "").strip())}
    except:
        return {"bi_json": {"error": "解析失败"}}