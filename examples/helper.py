from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.core import Repository


# --- Base ---
class Base(DeclarativeBase):
    pass


# --- Basic User (for 00_basic_crud) ---
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserRepository(Repository[User, UserSchema]):
    pass


# --- Task (for 01_manual_setup, 02_flux_setup) ---
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)


class TaskSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    completed: bool


class TaskCreate(BaseModel):
    title: str
    completed: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


# --- Metric (for 03_batch_operations, 04_parallel_execution) ---
class Metric(Base):
    __tablename__ = "metrics"
    id = Column(String, primary_key=True)
    name = Column(String)
    value = Column(Integer)


class MetricSchema(BaseModel):
    name: str
    value: int


class MetricRepository(Repository[Metric, MetricSchema]):
    pass


# --- Social (for 05_dataloader_n_plus_one) ---
class SocialUser(Base):
    __tablename__ = "social_users"
    id = Column(String, primary_key=True)
    name = Column(String)


class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True)
    title = Column(String)
    user_id = Column(String, ForeignKey("social_users.id"))


class SocialUserSchema(BaseModel):
    name: str


class PostSchema(BaseModel):
    title: str
    user_id: str


class SocialUserRepository(Repository[SocialUser, SocialUserSchema]):
    pass


class PostRepository(Repository[Post, PostSchema]):
    pass
