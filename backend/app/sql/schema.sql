-- Idempotent schema: safe to run multiple times

CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sub_topics (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE(topic_id, name)
);

CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    sub_topic_id INTEGER NOT NULL REFERENCES sub_topics(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    explanation TEXT,
    image_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_questions_sub_topic_id ON questions(sub_topic_id);

-- For efficient random-like selection within a sub_topic using id range scans
CREATE INDEX IF NOT EXISTS idx_questions_sub_topic_id_id ON questions(sub_topic_id, id);

CREATE TABLE IF NOT EXISTS choices (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    choice_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(question_id, choice_text)
);

CREATE INDEX IF NOT EXISTS idx_choices_question_id ON choices(question_id);

CREATE TABLE IF NOT EXISTS user_answers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    choice_id INTEGER REFERENCES choices(id) ON DELETE SET NULL,
    is_correct BOOLEAN NOT NULL,
    answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_answers_user_id ON user_answers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_question_id ON user_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_answered_at ON user_answers(answered_at);

-- Composite indexes to accelerate common filters and joins
CREATE INDEX IF NOT EXISTS idx_user_answers_user_id_answered_at ON user_answers(user_id, answered_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_answers_user_id_question_id ON user_answers(user_id, question_id);

