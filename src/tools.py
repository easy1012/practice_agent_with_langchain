from langchain.tools import tool

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