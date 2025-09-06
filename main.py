import random
from typing import Annotated
from typing_extensions import TypedDict
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
load_dotenv()
openai_client = wrap_openai(OpenAI())

class State(TypedDict):#创建一个stategraph
    # 会话消息，使用add_messages添加
    messages: Annotated[list, add_messages]
    # 随机秘密数字0-9
    secret: int
    # 是否已猜中
    done: bool

# 构建图
graph_builder = StateGraph(State)

# 导入llm
llm = init_chat_model(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    model_provider="openai",
    base_url="http://127.0.0.1:60640/v1",
    api_key="sk-noauth",
    temperature=0,
    max_tokens=8,
)
#注：还没写langsmith追踪多轮对话

# 初始节点：生成秘密数字以及设置prompt，返回类型为State
def init(state: State) -> State:
    # 生成0-9范围内的随机数字
    secret = random.randint(0, 9)
    # 初始化给llm发的prompt
    messages = [
        SystemMessage( # 系统消息
            content=(
                "You are playing a number guessing game. The secret integer is between 0 and 9. "
                "On each turn, reply with ONLY one digit (0-9), no words, no punctuation."
            )
        ),
        HumanMessage(content="Guess the number."),# 人类消息
    ]
    return {"messages": messages, "secret": secret, "done": False}

# 猜测节点：让模型基于当前 prompt 进行一次回答，返回类型为State
def guess(state: State) -> State:
    # 得到llm推理一次后回答
    resp = llm.invoke(state["messages"])
    # add_messages
    return {"messages": [resp]}

<<<<<<< HEAD
# 解析文本中的数字，返回类型为int型
def parse_digit(text: str) -> Optional[int]:
    # 找到文本中0-9的第一个数字
    m = re.search(r"[0-9]", text)
    return int(m.group()) if m else None

=======
>>>>>>> 473f9c5c1fccb579976262657affe2d984f60977
# 评估节点：解析模型输出并给出反馈或结束
@traceable
def evaluate(state: State) -> State:
    # messages的最后一条
    last = state["messages"][-1]
    # 获取最后一条信息的content属性并解析出数字
    # 用 structured_output 解析模型回复为数字
    result = llm.structured_output(
        schema={"guess": int},
        messages=[last]
    )
    guess = result.get("guess")
    # 如果guess等于state类中的secret，返回state类中的done为True
    if guess == state["secret"]:
        return {"done": True}
    # 要是不等于则依次判断是太小了还是太大了
    feedback = "too low" if guess < state["secret"] else "too high"
    # 反馈信息
    return {
        "messages": [
            HumanMessage(
                content=(
                    f"Your guess: {guess}. Feedback: {feedback}. Guess again and reply ONLY one digit."
                )
            )
        ]
    }

# 检查状态里的 done 标记；如果已完成（True）返回字符串 "end"，否则返回 "continue
def should_continue(state: State) -> str:
    return "end" if state.get("done") else "continue"

# 创建记忆检查点
memory = InMemorySaver()

# 添加节点
graph_builder.add_node("init", init)
graph_builder.add_node("guess", guess)
graph_builder.add_node("evaluate", evaluate)

#添加边
graph_builder.add_edge(START, "guess")
graph_builder.add_edge("guess", "evaluate")
graph_builder.add_conditional_edges("evaluate", should_continue, {"continue": "guess", "end": END})

# 编译图
graph = graph_builder.compile(checkpointer=memory)

# 用langgraph生成markdown流程图
def export_mermaid_md(output_path: str = "graph.md") -> None:
    mermaid = graph.get_graph().draw_mermaid()
    Path("graph.md").write_text(f"[mermaid\n{mermaid}\n](http://_vscodecontentref_/1)\n", encoding="utf-8")

 

def main():
    # 极简运行入口：使用 thread_id 维持对话记忆
    thread_id = os.getenv("THREAD_ID", "1")
    config = {"configurable": {"thread_id": thread_id}}
    export_mermaid_md()
    for event in graph.stream({"messages": []}, config, stream_mode="values"):
        messages = event.get("messages", [])
        if messages:
            msg = messages[-1]
            content = getattr(msg, "content", None)
            if content:
                print(content)

if __name__ == "__main__":
    main()