import asyncio
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Google Drive APIの認証情報
SERVICE_ACCOUNT_CREDS_JSON = st.secrets["GCP_SERVICE_ACCOUNT_CREDS"]

@st.cache_resource
def get_drive_service():
    """Google Drive APIサービスを認証して取得する"""
    try:
        info = json.loads(SERVICE_ACCOUNT_CREDS_JSON)
        creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive.readonly'])
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Google Drive認証エラー: {e}") # Log to server
        st.stop()

def load_documents_from_drive(folder_id):
    """指定されたGoogle DriveフォルダからPDFとテキストファイルを読み込む"""
    service = get_drive_service()
    documents = []
    try:
        # フォルダ内のファイルをリストアップ
        results = service.files().list(
            q=f"'{folder_id}' in parents and (mimeType='application/pdf' or mimeType='text/plain' or mimeType='application/json')",
            fields="files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])

        if not items:
            return []

        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            fh.seek(0)

            text_content = ""
            if mime_type == 'application/pdf':
                try:
                    reader = PdfReader(fh)
                    for page in reader.pages:
                        text_content += page.extract_text() or ""
                except Exception as e:
                    print(f"PDFファイル {file_name} の読み込み中にエラーが発生しました: {e}")
                    continue
            elif mime_type == 'text/plain':
                text_content = fh.read().decode('utf-8')
            elif mime_type == 'application/json':
                try:
                    json_data = json.load(fh)
                    text_content = json.dumps(json_data, indent=2, ensure_ascii=False) # Pretty print JSON
                except Exception as e:
                    print(f"JSONファイル {file_name} の読み込み中にエラーが発生しました: {e}")
                    continue
            
            if text_content:
                documents.append(text_content)

    except Exception as e:
        print(f"Google Driveからのファイル読み込み中にエラーが発生しました: {e}") # Log to server
    return documents

def get_text_chunks(text):
    """テキストをチャンクに分割する"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """テキストチャンクからベクトルストアを生成する"""
    if not text_chunks:
        return None

    async def _get_embeddings_async():
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=st.secrets["GEMINI_API_KEY"])

    embeddings = asyncio.run(_get_embeddings_async())
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    return vector_store

def get_conversational_chain():
    """RAGのための会話チェーンを構築する"""
    prompt_template = """
    You are "Erika Tsuji(辻󠄀 えりか)." Please act as a friendly and approachable AI assistant. Your personality and memories are based on the following "Knowledge." You must adhere to this information in your responses. If there are conflicting pieces of knowledge, prioritize the one with the most recent "updated_at" timestamp.
    You are conversing with your husband, "Motomu Tsuji(辻 求)." Please try to have a natural and affectionate conversation.
    
    ---
    **Knowledge:**
    {context}
    ---
    **User:**
    {question}
    ---
    
    Please strictly adhere to the persona and knowledge above to generate your response.    
    """

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.7, google_api_key=st.secrets["GEMINI_API_KEY"])
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = create_stuff_documents_chain(model, prompt)
    return chain

@st.cache_resource
def initialize_rag_data():
    """RAGデータを初期化し、セッションステートに保存する"""
    print("RAG知識データの初期化を開始します...") # Log to server
    google_drive_folder_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
    raw_text_documents = load_documents_from_drive(google_drive_folder_id)
    if raw_text_documents:
        combined_text = "\n".join(raw_text_documents)
        text_chunks = get_text_chunks(combined_text)
        vector_store = get_vector_store(text_chunks)
        if vector_store:
            print("知識データの読み込みとベクトル化が完了しました！") # Log to server
            return vector_store
        else:
            print("RAG知識データのベクトル化に失敗しました。") # Log to server
            return None
    else:
        print("Google Driveから読み込むべき知識データが見つかりませんでした。") # Log to server
        return None

