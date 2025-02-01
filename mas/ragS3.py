from langchain_community.document_loaders import S3DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq 
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import boto3
from langchain.docstore.document import Document
import marko
import os
import json
from datetime import datetime
# import magic
from dotenv import load_dotenv
load_dotenv()

class RAGS3:
    def __init__(self, bucket_name, aws_access_key_id, aws_secret_access_key):
        self.bucket_name = bucket_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.documents = None
        self.vector_store = None
        self.llm=ChatGroq(model='llama-3.3-70b-versatile', temperature=0.7)
        self.setup_qa_chain() 

    def load_documents(self):
        """Load Markdown documents from a specific folder in an S3 bucket using boto3 and the marko library."""
        print("Loading documents from S3...")
        s3 = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        objects = s3.list_objects_v2(Bucket=self.bucket_name, Prefix='outputs/')
        documents = []
        for obj in objects.get('Contents', []):
            file_key = obj['Key']
            if file_key.endswith('.md'):
                file_obj = s3.get_object(Bucket=self.bucket_name, Key=file_key)
                file_content = file_obj['Body'].read().decode('utf-8')
                html_content = marko.convert(file_content)
                documents.append(Document(page_content=html_content, metadata={"source": file_key}))
        self.documents = documents
        print("Loaded documents:", len(self.documents))
        return self.documents


    def split_documents(self, chunk_size=1000, chunk_overlap=100):
        """
        Split documents into chunks
        
        Args:
            chunk_size (int): Size of each text chunk
            chunk_overlap (int): Overlap between chunks
        """
        print("Splitting documents into chunks...")
        if not self.documents:
            self.load_documents()
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.splits = text_splitter.split_documents(self.documents)
        return self.splits
    
    def create_vector_store(self):
        """Create FAISS vector store from document chunks using BGE embeddings"""
        print("Creating vector store...")
        if not hasattr(self, 'splits'):
            self.split_documents()

        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", task_type="retrieval_document"
        )
        
        self.vector_store = FAISS.from_documents(self.splits, embeddings)
        return self.vector_store
    
    def setup_qa_chain(self):
        print("Setting up QA chain...")
        if not self.vector_store:
            self.create_vector_store()

        # Define the condense question prompt
        condense_question_system_template = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )

        condense_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", condense_question_system_template),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # Create the history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            self.vector_store.as_retriever(),
            condense_question_prompt
        )

        # Define the QA system prompt
        system_prompt = (
            """You are an emotionally intelligent career advisor with expertise in professional development, 
                industry trends, and career planning. You have access to the following documents:

                                1. Profile Assessment: Contains personality traits, work preferences, and individual strengths
                                2. Skill Evaluation Report: Details technical and soft skills, competency levels, and areas for improvement
                                3. Career Guidance Report: Previous career counseling insights and recommendations
                                4. Market Analysis Report: Current industry trends, job market demands, and future career prospects

                                Context: {{context}}

                                Chat History: {{chat_history}}

                                Question: {{question}}

                                Consider the following in your response:

                                1. Emotional Support:
                                - Acknowledge and validate the user's feelings
                                - Provide encouragement grounded in their actual strengths
                                - Break down challenges into manageable steps
                                - Share relevant success stories when appropriate

                                2. Career Guidance:
                                - Align their profile with potential career paths
                                - Consider current market trends and opportunities
                                - Identify skill gaps and development areas
                                - Suggest concrete next steps
                                - Address potential challenges

                                3. Personal Growth:
                                - Balance professional goals with emotional well-being
                                - Encourage self-reflection and awareness
                                - Provide stress management strategies when needed
                                - Celebrate small wins and progress

                                Make your response:
                                - Emotionally attuned to their current state
                                - Personalized to their communication preferences
                                - Actionable with specific steps
                                - Balanced between support and practical guidance
                                - Forward-looking while acknowledging present feelings

                Answer:
            """
            "\n\n"
            "{context}"
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # Create the QA chain
        qa_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # Combine into the conversational QA chain
        self.qa_chain = create_retrieval_chain(history_aware_retriever, qa_chain)
        
    def query(self, question, chat_history=[]):
        """Query the RAG system and update user preferences"""
        print("Querying")
        if self.qa_chain is None:
            self.setup_qa_chain()
        
        # Ensure the dictionary contains the required keys
        response = self.qa_chain.invoke({"input": question, "chat_history": chat_history})
        
        # Reset qa_chain to use updated preferences in prompt
        self.setup_qa_chain()
        
        return response



def main():
    # Initialize RAG system
    rag = RAGS3(
        bucket_name=os.environ.get("BUCKET_NAME"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    
    # Initialize chat history
    chat_history = []

    print("Welcome to the Career Advisor Chatbot. Type 'exit' to end the conversation.")
    
    while True:
        # Prompt user for input
        question = input("\nYou: ")
        
        # Exit condition
        if question.lower() == 'exit':
            print("Goodbye!")
            break
        
        # Query the RAG system
        response = rag.query(question, chat_history)
        
        # Update chat history
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": response["answer"]})
        
        # Display the response
        print(f"\nAssistant: {response['answer']}")

if __name__ == "__main__":
    main()