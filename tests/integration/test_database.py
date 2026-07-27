import pytest
from sqlalchemy import select

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentMetadata, DocumentStatus
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message, MessageRole
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.conversation_repository import ConversationRepository

pytestmark = pytest.mark.asyncio

async def test_database_connection(db_session):
    """Test that the database connection works."""
    result = await db_session.execute(select(1))
    assert result.scalar() == 1


async def test_user_creation(db_session):
    """Test user creation and retrieval via repository."""
    repo = UserRepository(db_session)
    user = User(email="test@example.com", username="testuser")
    
    created_user = await repo.create(user)
    assert created_user.id is not None
    assert created_user.email == "test@example.com"
    
    fetched_user = await repo.get_by_email("test@example.com")
    assert fetched_user is not None
    assert fetched_user.username == "testuser"


async def test_document_creation(db_session):
    """Test document and metadata creation via repository."""
    user_repo = UserRepository(db_session)
    user = await user_repo.create(User(email="docowner@example.com", username="docowner"))
    
    doc_repo = DocumentRepository(db_session)
    document = Document(
        user_id=user.id,
        filename="test.pdf",
        file_type="application/pdf",
        storage_path="docs/test.pdf",
        status=DocumentStatus.UPLOADED
    )
    
    created_doc = await doc_repo.create(document)
    assert created_doc.id is not None
    
    # Test Metadata
    metadata = DocumentMetadata(
        document_id=created_doc.id,
        title="Test PDF",
        page_count=5
    )
    created_metadata = await doc_repo.create_metadata(metadata)
    assert created_metadata.id is not None
    assert created_metadata.title == "Test PDF"


async def test_conversation_creation(db_session):
    """Test conversation and message creation via repository."""
    user_repo = UserRepository(db_session)
    user = await user_repo.create(User(email="chatuser@example.com", username="chatuser"))
    
    conv_repo = ConversationRepository(db_session)
    conversation = Conversation(
        user_id=user.id,
        title="Test Chat"
    )
    
    created_conv = await conv_repo.create(conversation)
    assert created_conv.id is not None
    assert created_conv.title == "Test Chat"
    
    # Add message
    message = Message(
        conversation_id=created_conv.id,
        role=MessageRole.USER,
        content="Hello AI"
    )
    created_message = await conv_repo.add_message(message)
    assert created_message.id is not None
    assert created_message.role == MessageRole.USER


async def test_relationship_integrity(db_session):
    """Test that relationships are correctly established."""
    user_repo = UserRepository(db_session)
    conv_repo = ConversationRepository(db_session)
    
    user = await user_repo.create(User(email="reluser@example.com", username="reluser"))
    
    conversation = await conv_repo.create(Conversation(user_id=user.id, title="Relationship Chat"))
    
    await conv_repo.add_message(Message(conversation_id=conversation.id, role=MessageRole.USER, content="Msg 1"))
    await conv_repo.add_message(Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="Msg 2"))
    
    # Fetch conversation with messages
    conv_with_msgs = await conv_repo.get_with_messages(conversation.id)
    assert conv_with_msgs is not None
    assert len(conv_with_msgs.messages) == 2
    assert conv_with_msgs.messages[0].content == "Msg 1"
    assert conv_with_msgs.messages[1].content == "Msg 2"
