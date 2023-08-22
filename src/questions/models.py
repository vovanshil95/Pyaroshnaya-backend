import uuid

from sqlalchemy import Column, UUID, String, BOOLEAN, ForeignKey

from history.models import Base

class Category(Base):
    __tablename__ = 'question_category'
    def __init__(self,
                 id: uuid.UUID,
                 title: str,
                 is_main_screen_presented: bool,
                 is_category_screen_presented: bool,
                 order_index: str,
                 description: str=None,
                 parent_id: uuid.UUID=None):
        self.id = id
        self.title = title
        self.description = description
        self.parent_id = parent_id
        self.is_main_screen_presented = is_main_screen_presented
        self.is_category_screen_presented = is_category_screen_presented
        self.order_index = order_index

    id=Column(UUID, primary_key=True)
    title=Column(String, nullable=False)
    description=Column(String)
    parent_id=Column(UUID)
    is_main_screen_presented = Column(BOOLEAN, nullable=False, default=False)
    is_category_screen_presented = Column(BOOLEAN, nullable=False, default=False)
    order_index = Column(String, nullable=False, unique=True)

class Prompt(Base):
    __tablename__ = 'prompt'
    def __init__(self, id: uuid.UUID, category_id: uuid.UUID, text: str, order_index: str):
        self.id = id
        self.category_id = category_id
        self.text = text
        self.order_index = order_index

    id = Column(UUID, primary_key=True)
    category_id = Column(ForeignKey('question_category.id', ondelete='cascade'))
    text = Column(String, nullable=False)
    order_index = Column(String, nullable=False)

class Question(Base):
    __tablename__ = 'question'
    def __init__(self,
                 id: uuid.UUID,
                 question_text: str,
                 is_required: bool,
                 category_id: uuid.UUID,
                 order_index: str,
                 snippet: str=None):
        self.id = id
        self.question_text = question_text
        self.is_required = is_required
        self.category_id = category_id
        self.snippet = snippet
        self.order_index = order_index

    id = Column(UUID, primary_key=True)
    question_text = Column(String, nullable=False)
    snippet = Column(String)
    is_required = Column(BOOLEAN, nullable=False)
    category_id = Column(ForeignKey('question_category.id', ondelete='cascade'), nullable=False)
    order_index = Column(String, nullable=False)

class Answer(Base):
    __tablename__ = 'answer'
    def __init__(self,
                 id: uuid.UUID,
                 question_id: uuid.UUID,
                 text: str,
                 user_id: uuid.UUID,
                 interaction_id: uuid.UUID=None):
        self.id = id
        self.question_id = question_id
        self.text = text
        self.user_id = user_id
        self.interaction_id = interaction_id
    id = Column(UUID, primary_key=True)
    question_id = Column(ForeignKey('question.id', ondelete='cascade'), nullable=False)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    interaction_id = Column(ForeignKey('gpt_interaction.id', ondelete='cascade'))
    text = Column(String, nullable=False)

class Option(Base):
    __tablename__ = 'option'
    def __init__(self, id: uuid.UUID, question_id: uuid.UUID, text: str):
        self.id = id
        self.question_id = question_id
        self.text = text
    id = Column(UUID, primary_key=True)
    question_id = Column(ForeignKey('question.id', ondelete='cascade'), nullable=False)
    text = Column(String, nullable=False)
