import os
from langchain_openai import ChatOpenAI

from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationBufferMemory
from tools import developer_tools
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model = 'gpt-5.1', reasoning={'effort':"none"})

memory = ConversationBufferMemory(memory_key = 'chat_history',
                                  return_messages = True)

def create_context_bundle(error_log, source_file_path):
    source_code = ""
    try:
        with open(source_file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    
    except Exception:
        source_code = f'Error: {source_file_path}를 읽을 수 없습니다.'
    
    return f"""
    당신의 임무는 아래 오류 로그와 관련 소스 코드를 분석하여 버그를 수정하는 것입니다.
    
    '''
    {error_log}
    '''
    
    '''python
    {source_code}
    '''
    
    """

def create_refactoring_agent(initial_context: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 숙련된 파이썬 개발자입니다. 주어진 컨텍스트를 바탕으로 버그를 수정하세요. ReadFile, WriteFile 도구를 사용하여 문제를 해결하세요. {initial_context}"""),
        (MessagesPlaceholder(variable_name='chat_history')),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name='agent_scratchpad')
    ])
    
    agent = create_openai_tools_agent(llm, developer_tools, prompt)
    agent_executor = AgentExecutor(
        agent = agent,
        tools = developer_tools,
        memory = memory,
        verbose = True
    )
    
    return agent_executor


if __name__ == "__main__":
    error_log_from_report = '''
    Traceback (most recent call last):
    File "buggy_project/main.py", line 11, in <module>
        total = calculate_total(cart)
    File "buggy_project/utils.py", line 11, in <module>
        total_price += iten['price'] * item['quantity']
    TypeError: can't multiply sequence by non-int of type 'str'
    '''
    
    source_file_to_fix = "buggy_project/utils.py"
    
    initial_context = create_context_bundle(error_log_from_report, source_file_to_fix)
    agent = create_refactoring_agent(initial_context)
    
    user_goal = "이 버그 리포트를 분석하고, 'utils.py' 파일의 TypeError를 수정해"
    
    agent_result = agent.invoke({'input' : user_goal})
    
    while True:
        feedback = input("수정이 올바른가요?").lower()
        if feedback in ['y', 'n']:
            print('피드백을 기록했습니다.')
            break
        else:
            print('y 또는 n으로만 입력해주세요.')