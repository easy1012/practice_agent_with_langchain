import os
import shutil
import json
import numpy as np
import chromadb

from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI,OpenAIEmbeddings

from utils.cromadb import ExperienceDB
load_dotenv()


def setup_project_environment():
    project_dir = 'buggy_project'
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    
    os.makedirs(project_dir)
    with open(os.path.join(project_dir, 'utils.py'), "w", encoding='utf-8') as f:
        f.write(
            """
            def calculate_total(cart_items)"
                total_price = 0
                for item in cart_item:
                    total_price += item['price] * item['quantity]
                return total_price
            """
        )
        
    with open(os.path.join(project_dir, 'main.py'), "w", encoding='utf-8') as f:
        f.write(
            """
            from utils import calculate_total


            cart = [
                {'name': '사과', 'price' : 1500, 'quantity' : 5},
                {'name': '바나나', 'price' : 3000, 'quantity' : 2},
            ]


            try:
                total = calculate_total(cart)
                print(f'총 합계 : {total}')
            except TypeError as e:
                print(f'오류가 발생했습니다.: {e}')
            """
        )
        


@tool
def read_file(file_path):
    """파일의 전체 내용을 읽을 때 사용합니다. 인수로는 파일 경로(문자열)를 받습니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
        
    except Exception as e:
        return f'파일 읽기 오류: {e}'
    

@tool
def write_file(file_path, content):
    '''파일에 새로운 내용을 쓰거나 수정할 때 사용합니다. 인수로는 파일 경로(문자열)을 받습니다.'''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f"{file_path}"
    
    except Exception as e:
        return f'파일 쓰기 오류: {e}'
    

developer_tools = [read_file, write_file]


class CodeRefactoringAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model = 'gpt-5.1', reasoning={'effort' : 'none'})
        self.embedding_model = os.getenv('EMBEDDING_MODEL_NAME')
        self.embedding_dim = int(os.getenv('EMBEDDING_MODEL_DIM'))
        self.embeddings = OpenAIEmbeddings(
            model = self.embedding_model,
            dimensions= self.embedding_dim
        )
        self.experience_db = ExperienceDB(persist_dir = 'experience_db',
                                          embeddings = self.embeddings)
    
    def create_context_bundle(self,error_log, source_file_path):
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
        
    def run(self, bug_report):
        print('버그 리포트 접수 작업 시작')
        initial_context = self.create_context_bundle(bug_report['error_log'],
                                                     bug_report['file_path'])
        
        reinforce_context = self.experience_db.query_experience(initial_context)
        memory = ConversationBufferMemory(memory_key = 'chat_history',
                                  return_messages = True)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 숙련된 파이썬 개발자입니다. 주어진 컨텍스트를 바탕으로 버그를 수정하세요. ReadFile, WriteFile 도구를 사용하여 문제를 해결하세요. {initial_context}"""),
            (MessagesPlaceholder(variable_name='chat_history')),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name='agent_scratchpad')
        ])
        
        agent = create_openai_tools_agent(self.llm, developer_tools, prompt)
        agent_executor = AgentExecutor(
            agent = agent,
            tools = developer_tools,
            memory = memory,
            verbose = True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        

        try:
            result = agent_executor.invoke({'input': bug_report['goal']})
            print(f"{result['output']}")
            
        except Exception as e:
            print(f'에이전트 실행 오류 {e}')
            
        
        while True:
            feedback = input("수정이 올바른가요?").lower()
            if feedback in ['y', 'n']:
                self.experience_db.add_experience(
                    text = str(memory.buffer),
                    metadata = {'feedback' : feedback.lower(), "original_query": initial_context}
                )
                break
            
            
if __name__ == "__main__":
    setup_project_environment()
    agent_manager = CodeRefactoringAgent()
    
    bug_report_1 = {
        'error_log' : '''
    Traceback (most recent call last):
    File "buggy_project/main.py", line 11, in <module>
        total = calculate_total(cart)
    File "buggy_project/utils.py", line 11, in <module>
        total_price += iten['price'] * item['quantity']
    TypeError: can't multiply sequence by non-int of type 'str'
    ''',
    'file_path' : "buggy_project/utils.py",
    'goal' : "이 버그 리포트를 분석하고, 'utils.py' 파일의 TypeError를 수정해"
    
    }
    
    agent_manager.run(bug_report_1)
            
            
