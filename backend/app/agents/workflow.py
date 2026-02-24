from langgraph.graph import StateGraph, END
from backend.app.agents.state import AgentState
from backend.app.agents.nodes import planner_node, reviewer_and_execute_node, bi_render_node

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node) # ⬅️ 改用新规划师
workflow.add_node("reviewer", reviewer_and_execute_node)
workflow.add_node("bi_render", bi_render_node)

workflow.set_entry_point("planner") # ⬅️ 入口变更为规划师
workflow.add_edge("planner", "reviewer")
workflow.add_edge("reviewer", "bi_render")
workflow.add_edge("bi_render", END)

app_workflow = workflow.compile()