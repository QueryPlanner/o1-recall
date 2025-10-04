from typing import List, Optional

from pydantic import BaseModel


class Topic(BaseModel):
    id: int
    name: str


class SubTopic(BaseModel):
    id: int
    name: str
    topic_id: int


class Choice(BaseModel):
    id: int
    question_id: int
    choice_text: str
    is_correct: bool


class Question(BaseModel):
    id: int
    sub_topic_id: int
    question_text: str
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    choices: List[Choice]


class AnswerRequest(BaseModel):
    question_id: int
    choice_id: int


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_choice_id: int


class StreakResponse(BaseModel):
    current_streak_days: int
    today_answers_count: int
    streak_goal: int = 5

